from datetime import UTC, datetime

from reconra.audit.events import decision_audit_event
from reconra.evidence.builder import CandidateEvidence
from reconra.policy.reconciliation import ReconciliationPolicy
from reconra.verification.risk import decide_resolution_action
from reconra.verification.verifier import (
    ProposalVerificationState,
    verify_proposal,
)

from agent.schemas.proposal import AgentProposal


def test_same_event_key_is_run_scoped_but_deterministic() -> None:
    """Material events from separate runs cannot share an identifier."""
    first = decision_audit_event(
        run_id="run-a", event_key="verification:case-1:attempt-1",
        timestamp=datetime(2026, 8, 29, tzinfo=UTC), actor="verifier",
        action="VERIFY_PROPOSAL", decision="VERIFIED", verification_status="VERIFIED",
        financial_impact_paise=100, exception_id="case-1", lifecycle_order=2,
    )
    identical = decision_audit_event(
        run_id="run-a", event_key="verification:case-1:attempt-1",
        timestamp=datetime(2026, 8, 29, tzinfo=UTC), actor="verifier",
        action="VERIFY_PROPOSAL", decision="VERIFIED", verification_status="VERIFIED",
        financial_impact_paise=100, exception_id="case-1", lifecycle_order=2,
    )
    other_run = decision_audit_event(
        run_id="run-b", event_key="verification:case-1:attempt-1",
        timestamp=datetime(2026, 8, 29, tzinfo=UTC), actor="verifier",
        action="VERIFY_PROPOSAL", decision="VERIFIED", verification_status="VERIFIED",
        financial_impact_paise=100, exception_id="case-1", lifecycle_order=2,
    )

    assert first.event_id == identical.event_id
    assert first.event_id != other_run.event_id


def test_reverification_and_repeated_risk_decisions_have_distinct_event_ids() -> None:
    candidate = CandidateEvidence(
        source_id="settlement-1", candidate_id="bank-1", amount_delta_paise=0,
        date_delta_days=0, utr_similarity=0.95, narration_similarity=None,
        exact_amount=True, normalized_similarity=0.95,
        evidence=("fuzzy_utr", "exact_amount", "date_within_policy_window"),
    )
    proposal = AgentProposal(
        case_id="case-1", break_class="MANGLED_UTR", hypothesis="reference differs",
        candidate_resolution={"source_id": "settlement-1", "candidate_id": "bank-1"},
        confidence=0.8, evidence=["fuzzy_utr"], recommended_action="REQUEST_REVIEW",
    )
    state = ProposalVerificationState(
        case_evidence={"case-1": {"fuzzy_utr"}},
        case_candidates={"case-1": (candidate,)},
        case_impacts_paise={"case-1": 100},
        available_unexplained_paise=100,
    )
    policy = ReconciliationPolicy(high_impact_review_threshold_paise=100)
    audit_events = []

    first = verify_proposal(proposal, state, policy, run_id="run-1", audit_events=audit_events)
    second = verify_proposal(proposal, state, policy, run_id="run-1", audit_events=audit_events)
    decide_resolution_action(proposal, first, policy, run_id="run-1", audit_events=audit_events)
    decide_resolution_action(proposal, second, policy, run_id="run-1", audit_events=audit_events)

    assert audit_events[0].event_id != audit_events[1].event_id
    assert audit_events[2].event_id != audit_events[3].event_id
    assert len({event.event_id for event in audit_events}) == 4
