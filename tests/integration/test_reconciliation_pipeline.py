from __future__ import annotations

import ast
from copy import deepcopy
from pathlib import Path

import pytest
from reconra.models.exception import BreakClass
from reconra.policy.reconciliation import ReconciliationPolicy
from reconra.reconciliation.pipeline import (
    CanonicalDataset,
    ReconciliationStage,
    reconcile_deterministic,
)

from generator.src.clean import generate_clean_dataset
from generator.src.config import DatasetRole
from generator.src.roles import generate_dataset


def test_clean_raw_inputs_complete_the_deterministic_pipeline_with_an_exact_tie_out() -> None:
    """Fails if an exact settlement-to-bank decision no longer explains its bank credit."""
    raw_inputs = generate_clean_dataset(seed=1101).raw_inputs

    result = reconcile_deterministic(
        CanonicalDataset.from_raw_inputs(raw_inputs),
        ReconciliationPolicy(),
    )

    assert result.completed is True
    assert result.unexplained_residual_paise == 0
    assert result.total_bank_credit_paise == result.explained_bank_credit_paise
    assert result.exceptions == []
    assert len(result.payment_matches) == 64
    assert len(result.settlement_bank_matches) == 8
    assert result.stages == [
        ReconciliationStage.VALIDATED.value,
        ReconciliationStage.NORMALIZED.value,
        ReconciliationStage.GROUPED_SETTLEMENTS.value,
        ReconciliationStage.EXACT_MATCHING_COMPLETE.value,
        ReconciliationStage.DETERMINISTIC_COMPLETE.value,
    ]
    assert result.audit_events
    assert {event.actor for event in result.audit_events} == {"rule_engine"}
    assert all(event.verification_status == "VERIFIED" for event in result.audit_events)


def test_fuzzy_discovery_leaves_an_unmatched_bank_credit_as_an_explicit_residual() -> None:
    """Fails if fuzzy text evidence is ever promoted into an automatic financial match."""
    raw_inputs = deepcopy(generate_clean_dataset(seed=1101).raw_inputs)
    raw_inputs["bank_transactions"][0]["utr"] = "UTR CLEAN 00"

    result = reconcile_deterministic(
        CanonicalDataset.from_raw_inputs(raw_inputs),
        ReconciliationPolicy(settlement_date_window_days=0),
    )

    expected_residual = raw_inputs["bank_transactions"][0]["credit_paise"]
    assert type(expected_residual) is int
    assert result.unexplained_residual_paise == expected_residual
    assert result.explained_bank_credit_paise + expected_residual == result.total_bank_credit_paise
    assert [exception.break_class for exception in result.exceptions] == [
        BreakClass.UNRESOLVABLE,
        BreakClass.MISSING_BANK_CREDIT,
    ]
    bank_residual, missing_bank_credit = result.exceptions
    assert bank_residual.financial_impact_paise == expected_residual
    assert bank_residual.evidence == [
        "bank_transaction_id:bank_clean_000",
        "fuzzy_candidate_discovered",
    ]
    assert missing_bank_credit.financial_impact_paise == 0
    assert "settlement_id:setl_clean_000" in missing_bank_credit.evidence
    assert "no_exact_bank_evidence" in missing_bank_credit.evidence
    assert any(
        event.action == "CANDIDATE_DISCOVERY"
        and event.exception_id == bank_residual.exception_id
        and event.decision == "CANDIDATES_FOUND"
        for event in result.audit_events
    )


def test_missing_bank_evidence_creates_settlement_exceptions_without_changing_bank_tie_out() -> (
    None
):
    """Fails if an unmatched settlement is silently dropped or treated as invented bank money."""
    raw_inputs = deepcopy(generate_clean_dataset(seed=1101).raw_inputs)
    raw_inputs["bank_transactions"] = []

    result = reconcile_deterministic(
        CanonicalDataset.from_raw_inputs(raw_inputs),
        ReconciliationPolicy(),
    )

    assert result.total_bank_credit_paise == 0
    assert result.explained_bank_credit_paise == 0
    assert result.unexplained_residual_paise == 0
    assert len(result.exceptions) == 8
    assert {exception.break_class for exception in result.exceptions} == {
        BreakClass.MISSING_BANK_CREDIT
    }
    assert {exception.financial_impact_paise for exception in result.exceptions} == {0}
    assert (
        len([event for event in result.audit_events if event.action == "MISSING_BANK_CREDIT"]) == 8
    )


def test_unmatched_payment_and_settlement_evidence_are_escalated_without_affecting_bank_money() -> (
    None
):
    """Fails if source-evidence gaps are hidden after a bank row still ties out."""
    raw_inputs = deepcopy(generate_clean_dataset(seed=1101).raw_inputs)
    raw_inputs["reconciliation_rows"][0]["payment_id"] = "pay_missing_from_settlement"

    result = reconcile_deterministic(
        CanonicalDataset.from_raw_inputs(raw_inputs),
        ReconciliationPolicy(),
    )

    assert result.unexplained_residual_paise == 0
    assert {exception.break_class for exception in result.exceptions} == {
        BreakClass.MISSING_SETTLEMENT,
        BreakClass.MISSING_PAYMENT,
    }
    assert {exception.financial_impact_paise for exception in result.exceptions} == {0}


def test_identical_duplicate_order_is_visible_without_changing_the_bank_tie_out() -> None:
    """Fails if heldout duplicate-ledger evidence blocks the run or is silently hidden."""
    raw_inputs = generate_dataset(DatasetRole.HELDOUT).raw_inputs

    result = reconcile_deterministic(
        CanonicalDataset.from_raw_inputs(raw_inputs),
        ReconciliationPolicy(),
    )

    duplicate_exceptions = [
        exception
        for exception in result.exceptions
        if exception.break_class is BreakClass.DUPLICATE_LEDGER_ROW
    ]
    assert result.completed is True
    assert len(duplicate_exceptions) == 1
    duplicate_exception = duplicate_exceptions[0]
    assert duplicate_exception.exception_id == "duplicate-order-order_clean_004"
    assert duplicate_exception.financial_impact_paise == 0
    assert duplicate_exception.evidence == [
        "order_id:order_clean_004",
        "identical_canonical_order_rows",
    ]
    assert any(
        event.action == "DUPLICATE_LEDGER_ROW"
        and event.exception_id == duplicate_exception.exception_id
        and event.financial_impact_paise == 0
        for event in result.audit_events
    )
    assert result.total_bank_credit_paise == (
        result.explained_bank_credit_paise + result.unexplained_residual_paise
    )


def test_non_identical_duplicate_order_is_rejected_conservatively() -> None:
    """Fails if conflicting duplicate ledger evidence is accepted as an exact duplicate."""
    raw_inputs = deepcopy(generate_clean_dataset(seed=1101).raw_inputs)
    conflicting_order = deepcopy(raw_inputs["orders"][0])
    conflicting_order["amount_paise"] += 1
    raw_inputs["orders"].append(conflicting_order)

    with pytest.raises(ValueError, match="conflicting duplicate order_id"):
        reconcile_deterministic(
            CanonicalDataset.from_raw_inputs(raw_inputs),
            ReconciliationPolicy(),
        )


def test_engine_pipeline_has_no_agent_import_or_static_agent_call() -> None:
    """Fails if deterministic production code acquires an agent dependency before review."""
    engine_root = Path(__file__).resolve().parents[2] / "engine" / "reconra"
    violations: list[str] = []
    for source_file in engine_root.rglob("*.py"):
        tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
        violations.extend(_agent_dependency_violations(tree))

    assert violations == []


@pytest.mark.parametrize(
    ("source", "expected_violation"),
    [
        ("from reconra.agent import reasoner", "import:reconra.agent"),
        (
            "from importlib import import_module\nimport_module('reconra.agent.reasoner')",
            "dynamic-import:reconra.agent.reasoner",
        ),
        ("agent.reason()", "call:agent.reason"),
    ],
)
def test_agent_free_guard_detects_nested_imports_dynamic_imports_and_rooted_calls(
    source: str,
    expected_violation: str,
) -> None:
    """Fails if the static guard regresses to only direct agent imports or calls."""
    assert _agent_dependency_violations(ast.parse(source)) == [expected_violation]


def _agent_dependency_violations(tree: ast.AST) -> list[str]:
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            violations.extend(
                f"import:{alias.name}"
                for alias in node.names
                if _module_path_contains_agent(alias.name)
            )
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            if _module_path_contains_agent(node.module):
                violations.append(f"import:{node.module}")
        elif isinstance(node, ast.Call):
            function_path = _expression_path(node.func)
            if function_path in {"import_module", "importlib.import_module", "__import__"}:
                if node.args and isinstance(node.args[0], ast.Constant):
                    module_path = node.args[0].value
                    if isinstance(module_path, str) and _module_path_contains_agent(module_path):
                        violations.append(f"dynamic-import:{module_path}")
            elif _call_root(node.func) == "agent":
                violations.append(f"call:{function_path}")
    return violations


def _module_path_contains_agent(module_path: str) -> bool:
    return "agent" in module_path.split(".")


def _expression_path(expression: ast.expr) -> str:
    if isinstance(expression, ast.Name):
        return expression.id
    if isinstance(expression, ast.Attribute):
        return f"{_expression_path(expression.value)}.{expression.attr}"
    return "<dynamic>"


def _call_root(expression: ast.expr) -> str | None:
    if isinstance(expression, ast.Name):
        return expression.id
    if isinstance(expression, ast.Attribute):
        return _call_root(expression.value)
    return None
