from datetime import UTC, datetime
from json import loads

from reconra.artifacts.audit import write_audit_log
from reconra.artifacts.exceptions import write_exception_worklist
from reconra.artifacts.ledger import write_reconciled_ledger
from reconra.artifacts.summary import write_reconciliation_summary
from reconra.audit.events import AuditEvent
from reconra.metrics.evaluator import EvaluationReport
from reconra.models.exception import BreakClass, ReconciliationException, ResolutionStatus
from reconra.models.result import DeterministicMatch, ReconciliationResult


def _result() -> ReconciliationResult:
    return ReconciliationResult(
        run_id="run-1",
        total_bank_credit_paise=123_456,
        explained_bank_credit_paise=120_000,
        unexplained_residual_paise=3_456,
        payment_matches=[
            DeterministicMatch(
                source_id="payment-2",
                candidate_id="settlement-2",
                evidence=["payment_id"],
            ),
            DeterministicMatch(
                source_id="payment-1",
                candidate_id="settlement-1",
                evidence=["payment_id"],
            ),
        ],
        exceptions=[
            ReconciliationException(
                exception_id="exception-1",
                break_class=BreakClass.MISSING_BANK_CREDIT,
                resolution_status=ResolutionStatus.ESCALATED,
                financial_impact_paise=3_456,
                evidence=["settlement_id:settlement-3"],
            )
        ],
        audit_events=[
            AuditEvent(
                event_id="event-1",
                run_id="run-1",
                timestamp=datetime(2026, 1, 1, tzinfo=UTC),
                actor="rule_engine",
                action="ESCALATED",
                decision="ESCALATED",
                verification_status="NOT_APPLIED",
                financial_impact_paise=3_456,
            )
        ],
        completed=True,
    )


def test_artifact_exports_are_deterministic_and_keep_paise_as_integer_values(tmp_path) -> None:
    result = _result()
    metrics = EvaluationReport.empty(total_records=2)

    ledger_path = write_reconciled_ledger(result, tmp_path)
    worklist_path = write_exception_worklist(result, tmp_path)
    audit_path = write_audit_log(result, tmp_path)
    summary_path = write_reconciliation_summary(result, metrics, tmp_path)

    assert ledger_path.name == "reconciled_ledger.csv"
    ledger_lines = ledger_path.read_text(encoding="utf-8").splitlines()
    assert ledger_lines[1].startswith("payment,payment-1,settlement-1")
    assert "0.00" in ledger_lines[1]
    assert (
        worklist_path.read_text(encoding="utf-8")
        .splitlines()[1]
        .startswith("exception-1,MISSING_BANK_CREDIT,ESCALATED,3456,34.56")
    )
    audit_rows = loads(audit_path.read_text(encoding="utf-8"))
    assert audit_rows[0]["financial_impact_paise"] == 3456
    summary = loads(summary_path.read_text(encoding="utf-8"))
    assert summary["bank_credit"]["total_paise"] == 123456
    assert summary["bank_credit"]["residual_paise"] == 3456
    assert summary["bank_credit"]["total_display"] == "1,234.56"
    assert summary["metrics"]["scoring_available"] is False
    for field_name in (
        "coverage",
        "auto_resolution_precision",
        "false_match_rate",
        "resolvable_record_recall",
        "correct_abstention_rate",
        "per_break_class_accuracy",
    ):
        assert summary["metrics"][field_name] is None


def test_unscored_result_metrics_and_summary_retain_operational_activity(tmp_path) -> None:
    """Unscored runs must retain result-derived counters while truth rates remain unavailable."""
    result = ReconciliationResult(
        run_id="run-operational",
        total_bank_credit_paise=10_000,
        explained_bank_credit_paise=8_000,
        unexplained_residual_paise=2_000,
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
                financial_impact_paise=8_000,
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
                financial_impact_paise=2_000,
            ),
        ],
        completed=True,
    )

    metrics = EvaluationReport.empty(total_records=3).with_result(result)
    summary_path = write_reconciliation_summary(result, metrics, tmp_path)
    summary = loads(summary_path.read_text(encoding="utf-8"))

    assert metrics.total_records == 3
    assert metrics.resolved_records == 1
    assert metrics.deterministic_resolved == 1
    assert metrics.review_required == 1
    assert metrics.escalated == 1
    assert metrics.operational_outcome_count == 4
    assert summary["metrics"]["total_records"] == 3
    assert summary["metrics"]["resolved_records"] == 1
    assert summary["metrics"]["deterministic_resolved"] == 1
    assert summary["metrics"]["review_required"] == 1
    assert summary["metrics"]["escalated"] == 1
    assert summary["metrics"]["operational_outcome_count"] == 4
    assert summary["bank_credit"] == {
        "total_paise": 10_000,
        "explained_paise": 8_000,
        "residual_paise": 2_000,
        "total_display": "100.00",
        "explained_display": "80.00",
        "residual_display": "20.00",
    }
