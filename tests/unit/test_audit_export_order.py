from datetime import UTC, datetime
from json import loads
from pathlib import Path

from reconra.artifacts.audit import write_audit_log
from reconra.audit.events import decision_audit_event
from reconra.models.result import ReconciliationResult
from reconra.policy.reconciliation import ReconciliationPolicy
from reconra.reconciliation.pipeline import CanonicalDataset, reconcile_deterministic


def test_audit_export_orders_material_lifecycle_chronologically(tmp_path) -> None:
    events = [
        decision_audit_event(
            run_id="run-1", event_key="risk", timestamp=datetime(2026, 8, 29, 0, 3, tzinfo=UTC),
            actor="system", action="SYSTEM_AUTO_APPLY", decision="AUTO_RESOLVED",
            verification_status="VERIFIED", financial_impact_paise=100, lifecycle_order=4,
        ),
        decision_audit_event(
            run_id="run-1", event_key="auto", timestamp=datetime(2026, 8, 29, tzinfo=UTC),
            actor="agent", action="AGENT_PROPOSAL", decision="PROPOSED",
            verification_status="NOT_APPLIED", financial_impact_paise=100, lifecycle_order=1,
        ),
        decision_audit_event(
            run_id="run-1", event_key="verify", timestamp=datetime(2026, 8, 29, 0, 2, tzinfo=UTC),
            actor="risk_gate", action="RISK_DISPOSITION", decision="AUTO_RESOLVED",
            verification_status="VERIFIED", financial_impact_paise=100, lifecycle_order=3,
        ),
        decision_audit_event(
            run_id="run-1", event_key="proposal", timestamp=datetime(2026, 8, 29, 0, 1, tzinfo=UTC),
            actor="verifier", action="VERIFY_PROPOSAL", decision="VERIFIED",
            verification_status="VERIFIED", financial_impact_paise=100, lifecycle_order=2,
        ),
    ]
    result = ReconciliationResult(
        run_id="run-1", total_bank_credit_paise=100, explained_bank_credit_paise=100,
        unexplained_residual_paise=0, audit_events=events, completed=True,
    )

    path = write_audit_log(result, tmp_path)

    assert [row["action"] for row in loads(path.read_text(encoding="utf-8"))] == [
        "AGENT_PROPOSAL", "VERIFY_PROPOSAL", "RISK_DISPOSITION", "SYSTEM_AUTO_APPLY"
    ]


def test_pipeline_audit_events_receive_and_export_stable_lifecycle_order(tmp_path) -> None:
    """Same-timestamp deterministic events must not fall back to hash order."""
    input_directory = Path(__file__).resolve().parents[2] / "data" / "demo" / "input"
    dataset = CanonicalDataset.from_raw_inputs(
        {
            path.stem: loads(path.read_text(encoding="utf-8"))
            for path in input_directory.iterdir()
        }
    )
    result = reconcile_deterministic(dataset, ReconciliationPolicy())
    reversed_result = result.model_copy(
        update={"audit_events": list(reversed(result.audit_events))}
    )

    exported = loads(write_audit_log(reversed_result, tmp_path).read_text(encoding="utf-8"))

    assert [event.lifecycle_order for event in result.audit_events] == list(
        range(1, len(result.audit_events) + 1)
    )
    assert [row["lifecycle_order"] for row in exported] == list(
        range(1, len(exported) + 1)
    )
