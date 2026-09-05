from datetime import date

from reconra.audit.events import AuditEvent
from reconra.evidence.builder import build_evidence_packet
from reconra.policy.reconciliation import ReconciliationPolicy
from reconra.reconciliation.state import ReconciliationState

from agent import orchestrator
from agent.schemas.proposal import AgentProposal


def _packet():
    return build_evidence_packet(
        case_id="residual-1", target_amount_paise=100, target_date=date(2026, 8, 29),
        reference_fragments=(), related_refund_count=0, related_adjustment_count=0,
        unresolved_reason="residual", candidates=[{
            "source_id": "setl-1", "candidate_id": "candidate-1", "amount_delta_paise": 0,
            "date_delta_days": 0, "utr_similarity": 0.95, "narration_similarity": None,
            "exact_amount": True, "normalized_similarity": 0.95,
            "evidence": ("fuzzy_utr", "exact_amount", "date_within_policy_window"),
        }],
    )


def _proposal():
    return AgentProposal(
        case_id="residual-1", break_class="MANGLED_UTR", hypothesis="Reference differs.",
        candidate_resolution={"source_id": "setl-1", "candidate_id": "candidate-1"},
        confidence=1.0, evidence=["fuzzy_utr"], recommended_action="AUTO_RESOLVE",
    )


def test_successful_auto_apply_event_is_appended_after_authoritative_commit() -> None:
    state = ReconciliationState(100)
    observed_explained_paise: list[int] = []

    class _AuditEvents(list[AuditEvent]):
        def append(self, event: AuditEvent) -> None:
            if event.action == "SYSTEM_AUTO_APPLY":
                observed_explained_paise.append(state.explained_bank_credit_paise)
            super().append(event)

    audit_events = _AuditEvents()
    verification_state = orchestrator.verification_state_for_packets([_packet()], 100)

    assert orchestrator.apply_auto_resolution(
        state, "run-authoritative", _proposal(),
        ReconciliationPolicy(high_impact_review_threshold_paise=100), verification_state,
        audit_events=audit_events,
    )

    assert observed_explained_paise == [100]
    assert [event.action for event in audit_events] == [
        "VERIFY_PROPOSAL", "RISK_DISPOSITION", "SYSTEM_AUTO_APPLY"
    ]


def test_conservation_failure_is_audited_without_successful_auto_apply(monkeypatch) -> None:
    def force_conservation_failure(self) -> None:
        raise RuntimeError("forced")

    monkeypatch.setattr(
        ReconciliationState, "_assert_money_conservation", force_conservation_failure
    )
    state = ReconciliationState(100)
    verification_state = orchestrator.verification_state_for_packets([_packet()], 100)
    audit_events: list[AuditEvent] = []

    assert not orchestrator.apply_auto_resolution(
        state, "run-authoritative", _proposal(),
        ReconciliationPolicy(high_impact_review_threshold_paise=100), verification_state,
        audit_events=audit_events,
    )

    assert state.explained_bank_credit_paise == 0
    assert verification_state.committed_candidate_ids == set()
    assert any(event.action == "SYSTEM_AUTO_APPLY_FAILED" for event in audit_events)
    assert not any(event.action == "SYSTEM_AUTO_APPLY" for event in audit_events)
