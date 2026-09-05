from datetime import UTC, datetime
from json import loads

from reconra.artifacts.audit import write_audit_log
from reconra.audit.events import decision_audit_event
from reconra.policy.reconciliation import ReconciliationPolicy
from reconra.reconciliation.pipeline import CanonicalDataset, reconcile_deterministic


def test_pipeline_result_retains_the_service_owned_audit_collection(tmp_path) -> None:
    """Post-pipeline lifecycle events must remain visible through the final result."""
    audit_events = []
    result = reconcile_deterministic(
        CanonicalDataset(orders=(), payments=(), settlement_entries=(), bank_transactions=()),
        ReconciliationPolicy(), run_id="run-service", audit_events=audit_events,
    )
    audit_events.append(
        decision_audit_event(
            run_id="run-service", event_key="agent", timestamp=datetime(2026, 8, 29, tzinfo=UTC),
            actor="agent", action="AGENT_PROPOSAL", decision="PROPOSED",
            verification_status="NOT_APPLIED", financial_impact_paise=0, lifecycle_order=1,
        )
    )

    assert result.audit_events is audit_events
    assert result.audit_events[-1].action == "AGENT_PROPOSAL"
    assert [row["action"] for row in loads(
        write_audit_log(result, tmp_path).read_text(encoding="utf-8")
    )][-1] == "AGENT_PROPOSAL"
