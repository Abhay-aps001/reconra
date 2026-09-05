import asyncio
from datetime import date

from reconra.audit.events import AuditEvent
from reconra.evidence.builder import EvidencePacket, build_evidence_packet
from reconra.policy.reconciliation import ReconciliationPolicy
from reconra.reconciliation.state import ReconciliationState

from agent import orchestrator
from agent.schemas.proposal import AgentProposal


class _ReviewReasoner:
    async def reason(self, cases: list[EvidencePacket]) -> list[AgentProposal]:
        return [_proposal(cases[0].case_id, "REQUEST_REVIEW", 0.8)]


def _packet(case_id: str = "case-1") -> EvidencePacket:
    return build_evidence_packet(
        case_id=case_id, target_amount_paise=100, target_date=date(2026, 8, 29),
        reference_fragments=("UTR…1",), related_refund_count=0, related_adjustment_count=0,
        unresolved_reason="residual", candidates=[{
            "source_id": "setl-1", "candidate_id": "candidate-1", "amount_delta_paise": 0,
            "date_delta_days": 0, "utr_similarity": 0.95, "narration_similarity": None,
            "exact_amount": True, "normalized_similarity": 0.95,
            "evidence": ("fuzzy_utr", "exact_amount", "date_within_policy_window"),
        }],
    )


def _proposal(case_id: str, action: str = "AUTO_RESOLVE", confidence: float = 1.0) -> AgentProposal:
    return AgentProposal(
        case_id=case_id, break_class="MANGLED_UTR", hypothesis="Reference differs.",
        candidate_resolution={"source_id": "setl-1", "candidate_id": "candidate-1"},
        confidence=confidence, evidence=["fuzzy_utr"], recommended_action=action,
    )


def test_residual_proposal_retains_sanitized_review_context() -> None:
    packet = _packet()
    contexts = asyncio.run(
        orchestrator.reason_residuals(
            [packet], _ReviewReasoner(), ReconciliationPolicy(),
            available_unexplained_paise=100, run_id="run-1", audit_events=[],
        )
    )

    assert len(contexts) == 1
    assert contexts[0].disposition.value == "REVIEW_REQUIRED"
    assert contexts[0].packet.case_id == contexts[0].proposal.case_id


def test_residual_orchestration_passes_the_same_service_context_to_verifier_and_risk(
    monkeypatch,
) -> None:
    audit_events: list[AuditEvent] = []
    received_audits: list[list[AuditEvent]] = []
    received_run_ids: list[str] = []
    original_verify = orchestrator.verify_proposal
    original_risk = orchestrator.decide_resolution_action

    def capture_verification(*args, **kwargs):
        received_run_ids.append(kwargs["run_id"])
        received_audits.append(kwargs["audit_events"])
        return original_verify(*args, **kwargs)

    def capture_risk(*args, **kwargs):
        received_run_ids.append(kwargs["run_id"])
        received_audits.append(kwargs["audit_events"])
        return original_risk(*args, **kwargs)

    monkeypatch.setattr(orchestrator, "verify_proposal", capture_verification)
    monkeypatch.setattr(orchestrator, "decide_resolution_action", capture_risk)

    contexts = asyncio.run(
        orchestrator.reason_residuals(
            [_packet()], _ReviewReasoner(), ReconciliationPolicy(),
            available_unexplained_paise=100, run_id="run-service-owned", audit_events=audit_events,
        )
    )

    assert len(contexts) == 1
    assert received_run_ids == ["run-service-owned", "run-service-owned"]
    assert received_audits == [audit_events, audit_events]
    assert {event.action for event in audit_events} == {
        "AGENT_PROPOSAL", "VERIFY_PROPOSAL", "RISK_DISPOSITION"
    }


def test_valid_low_risk_proposal_applies_once_through_deterministic_state() -> None:
    state = ReconciliationState(100)
    verification_state = orchestrator.verification_state_for_packets([_packet()], 100)
    audit_events: list[AuditEvent] = []

    applied = orchestrator.apply_auto_resolution(
        state, "run-service-owned", _proposal("case-1"),
        ReconciliationPolicy(high_impact_review_threshold_paise=100), verification_state,
        audit_events=audit_events,
    )

    assert applied is True
    assert state.explained_bank_credit_paise == 100
    assert state.unexplained_residual_paise == 0
    assert verification_state.committed_candidate_ids == {"candidate-1"}
    assert {event.action for event in audit_events} == {
        "VERIFY_PROPOSAL", "RISK_DISPOSITION", "SYSTEM_AUTO_APPLY"
    }


def test_competing_auto_proposals_cannot_reuse_a_committed_candidate() -> None:
    state = ReconciliationState(100)
    verification_state = orchestrator.verification_state_for_packets([_packet()], 100)
    policy = ReconciliationPolicy(high_impact_review_threshold_paise=100)

    assert orchestrator.apply_auto_resolution(
        state, "run-1", _proposal("case-1"), policy, verification_state, audit_events=[]
    )
    assert not orchestrator.apply_auto_resolution(
        state, "run-2", _proposal("case-1"), policy, verification_state, audit_events=[]
    )
    assert state.explained_bank_credit_paise == 100
