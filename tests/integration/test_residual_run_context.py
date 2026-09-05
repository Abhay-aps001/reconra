from datetime import UTC, datetime

from app.services import reconciliation_service
from reconra.audit.events import AuditEvent, decision_audit_event

from agent import orchestrator


def test_production_residual_orchestration_uses_one_service_owned_context_per_run(
    monkeypatch,
) -> None:
    """The run ID and event collector retain one service-owned lifecycle per run."""
    received: list[tuple[str, list[AuditEvent]]] = []

    async def capture_residual_context(
        packets, reasoner, policy, *, available_unexplained_paise: int,
        run_id: str, audit_events: list[AuditEvent],
    ) -> list[object]:
        del packets, reasoner, policy, available_unexplained_paise
        audit_events.append(
            decision_audit_event(
                run_id=run_id, event_key="captured-agent", timestamp=datetime.now(UTC),
                actor="agent", action="AGENT_PROPOSAL", decision="PROPOSED",
                verification_status="NOT_APPLIED", financial_impact_paise=0,
            )
        )
        received.append((run_id, audit_events))
        return []

    monkeypatch.setattr(orchestrator, "reason_residuals", capture_residual_context)

    first_response = reconciliation_service.reconcile_demo()
    second_response = reconciliation_service.reconcile_demo()

    assert [run_id for run_id, _ in received] == [
        first_response["run_id"], second_response["run_id"]
    ]
    assert received[0][1] is not received[1][1]
    assert first_response["audit_events"][-1]["action"] == "AGENT_PROPOSAL"
    stored = reconciliation_service.get_run(first_response["run_id"])
    assert stored is not None
    assert stored["audit_events"] == first_response["audit_events"]
