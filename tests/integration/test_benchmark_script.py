import importlib.util
from pathlib import Path

from reconra.metrics.evaluator import EvaluationReport
from reconra.models.exception import BreakClass, ReconciliationException, ResolutionStatus
from reconra.models.result import DeterministicMatch, ReconciliationResult


def _benchmark_module():
    path = Path(__file__).resolve().parents[2] / "scripts" / "run_benchmark.py"
    specification = importlib.util.spec_from_file_location("task10_benchmark", path)
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_benchmark_accepts_direct_selected_dataset_artifacts(tmp_path) -> None:
    benchmark = _benchmark_module()
    for source_name in ("orders", "payments", "reconciliation_rows", "bank_transactions"):
        (tmp_path / f"{source_name}.json").write_text("[]", encoding="utf-8")

    assert benchmark._dataset_directory(tmp_path, "heldout") == tmp_path


def test_unscored_benchmark_payload_omits_truth_derived_rates() -> None:
    benchmark = _benchmark_module()

    payload = benchmark._benchmark_payload(
        dataset="heldout",
        mode="deterministic",
        output_directory=Path("artifact-output"),
        result=_ResultStub(),
        metrics=EvaluationReport.empty(total_records=4),
    )

    assert payload["scoring_available"] is False
    assert {
        "coverage",
        "auto_resolution_precision",
        "false_match_rate",
        "resolvable_record_recall",
        "correct_abstention_rate",
        "per_break_class_accuracy",
    }.isdisjoint(payload)


def test_unscored_benchmark_payload_includes_result_derived_operational_counts() -> None:
    benchmark = _benchmark_module()
    result = ReconciliationResult(
        run_id="run-benchmark",
        total_bank_credit_paise=500,
        explained_bank_credit_paise=400,
        unexplained_residual_paise=100,
        payment_matches=[
            DeterministicMatch(
                source_id="payment-1",
                candidate_id="settlement-1",
                evidence=["payment_id"],
            )
        ],
        settlement_bank_matches=[
            DeterministicMatch(
                source_id="settlement-1",
                candidate_id="bank-1",
                evidence=["settlement_utr"],
                financial_impact_paise=400,
            )
        ],
        exceptions=[
            ReconciliationException(
                exception_id="review-1",
                break_class=BreakClass.UNRESOLVABLE,
                resolution_status=ResolutionStatus.REVIEW_REQUIRED,
                financial_impact_paise=0,
            ),
            ReconciliationException(
                exception_id="escalated-1",
                break_class=BreakClass.MISSING_BANK_CREDIT,
                resolution_status=ResolutionStatus.ESCALATED,
                financial_impact_paise=100,
            ),
        ],
        completed=True,
    )
    metrics = EvaluationReport.empty(total_records=3).with_result(result)

    payload = benchmark._benchmark_payload(
        dataset="heldout",
        mode="deterministic",
        output_directory=Path("artifact-output"),
        result=result,
        metrics=metrics,
    )

    assert payload["total_records"] == 3
    assert payload["resolved_records"] == 1
    assert payload["deterministic_resolved"] == 1
    assert payload["review_required"] == 1
    assert payload["escalated"] == 1
    assert payload["operational_outcome_count"] == 4


class _ResultStub:
    total_bank_credit_paise = 300
    explained_bank_credit_paise = 200
    unexplained_residual_paise = 100
