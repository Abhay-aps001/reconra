"""Internal residual-reasoning orchestration."""

from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime

from reconra.audit.events import AuditEvent, decision_audit_event
from reconra.evidence.builder import EvidencePacket
from reconra.policy.reconciliation import ReconciliationPolicy
from reconra.reconciliation.state import ReconciliationState
from reconra.verification.idempotency import apply_resolution_once
from reconra.verification.risk import ResolutionDisposition, decide_resolution_action
from reconra.verification.verifier import (
    ProposalVerificationState,
    VerificationResult,
    verify_proposal,
)

from agent.reasoner import ResidualReasoner
from agent.schemas.proposal import AgentProposal, ReasoningAvailability


@dataclass(frozen=True, slots=True)
class ResidualApprovalContext:
    packet: EvidencePacket
    proposal: AgentProposal
    verification: VerificationResult
    disposition: ResolutionDisposition


def verification_state_for_packets(
    packets: list[EvidencePacket], available_unexplained_paise: int, *,
    committed_candidate_ids: set[str] | None = None,
) -> ProposalVerificationState:
    """Bind verification exclusively to candidates already discovered for each case."""
    return ProposalVerificationState(
        case_evidence={
            packet.case_id: {
                evidence for candidate in packet.candidates for evidence in candidate.evidence
            }
            for packet in packets
        },
        case_candidates={packet.case_id: packet.candidates for packet in packets},
        case_impacts_paise={packet.case_id: packet.target_amount_paise for packet in packets},
        available_unexplained_paise=available_unexplained_paise,
        committed_candidate_ids=(
            committed_candidate_ids if committed_candidate_ids is not None else set()
        ),
    )


async def reason_residuals(
    packets: list[EvidencePacket],
    reasoner: ResidualReasoner,
    policy: ReconciliationPolicy,
    *,
    available_unexplained_paise: int,
    run_id: str,
    audit_events: list[AuditEvent],
) -> list[ResidualApprovalContext]:
    """Reason only over sanitized residual packets and verify every proposal deterministically."""
    proposals = await reasoner.reason(packets)
    packets_by_case = {packet.case_id: packet for packet in packets}
    verification_state = verification_state_for_packets(packets, available_unexplained_paise)
    contexts: list[ResidualApprovalContext] = []
    for proposal in proposals:
        packet = packets_by_case.get(proposal.case_id)
        if packet is None:
            continue
        if proposal.availability is not ReasoningAvailability.UNAVAILABLE:
            proposal_attempt = _lifecycle_attempt(
                audit_events, run_id, proposal.case_id, "AGENT_PROPOSAL"
            )
            audit_events.append(
                decision_audit_event(
                    run_id=run_id,
                    event_key=(
                        f"proposal:{run_id}:{proposal.case_id}:"
                        f"{proposal_attempt}"
                    ),
                    timestamp=datetime.now(UTC),
                    actor="agent",
                    action="AGENT_PROPOSAL",
                    decision="PROPOSED",
                    verification_status="NOT_APPLIED",
                    financial_impact_paise=_proposal_impact_paise(
                        proposal, verification_state
                    ),
                    exception_id=proposal.case_id,
                    evidence=_known_evidence(
                        proposal.evidence, verification_state.case_evidence, proposal.case_id
                    ),
                    lifecycle_order=len(audit_events) + 1,
                )
            )
        verification = verify_proposal(
            proposal, verification_state, policy, run_id=run_id, audit_events=audit_events
        )
        disposition = decide_resolution_action(
            proposal, verification, policy, run_id=run_id, audit_events=audit_events
        )
        if disposition is ResolutionDisposition.REVIEW_REQUIRED:
            contexts.append(ResidualApprovalContext(packet, proposal, verification, disposition))
    return contexts


def apply_auto_resolution(
    state: ReconciliationState,
    run_id: str,
    proposal: AgentProposal,
    policy: ReconciliationPolicy,
    verification_state: ProposalVerificationState,
    *,
    audit_events: list[AuditEvent],
    human_approved: bool = False,
) -> bool:
    """Apply a verified automatic or human-approved review proposal transactionally."""
    verification_state.available_unexplained_paise = state.unexplained_residual_paise
    verification = verify_proposal(
        proposal, verification_state, policy, run_id=run_id, audit_events=audit_events
    )
    disposition = decide_resolution_action(
        proposal, verification, policy, run_id=run_id, audit_events=audit_events
    )
    if disposition is not ResolutionDisposition.AUTO_RESOLVED and not (
        human_approved and disposition is ResolutionDisposition.REVIEW_REQUIRED
    ):
        return False
    candidate = proposal.candidate_resolution
    if candidate is None:
        return False
    before_state = _state_snapshot(state)
    staged_state = deepcopy(state)
    resolution_action = "HUMAN_APPROVED" if human_approved else "AUTO_RESOLVED"
    apply_action = "SYSTEM_HUMAN_APPLY" if human_approved else "SYSTEM_AUTO_APPLY"
    failed_apply_action = (
        "SYSTEM_HUMAN_APPLY_FAILED" if human_approved else "SYSTEM_AUTO_APPLY_FAILED"
    )
    try:
        applied = apply_resolution_once(
            staged_state,
            run_id,
            proposal.case_id,
            resolution_action,
            verification.financial_impact_paise,
        )
        staged_state._assert_money_conservation()
    except (RuntimeError, ValueError) as error:
        failure_attempt = _lifecycle_attempt(
            audit_events, run_id, proposal.case_id, failed_apply_action
        )
        audit_events.append(
            decision_audit_event(
                run_id=run_id,
                event_key=(
                    f"{resolution_action.lower()}-apply-failed:{run_id}:{proposal.case_id}:"
                    f"{failure_attempt}"
                ),
                timestamp=datetime.now(UTC),
                actor="system",
                action=failed_apply_action,
                decision=(
                    "INVARIANT_FAILED" if isinstance(error, RuntimeError) else "APPLICATION_FAILED"
                ),
                verification_status="FAILED",
                financial_impact_paise=verification.financial_impact_paise,
                exception_id=proposal.case_id,
                evidence=_known_evidence(
                    proposal.evidence, verification_state.case_evidence, proposal.case_id
                ),
                before_state=before_state,
                after_state=_state_snapshot(state),
                lifecycle_order=len(audit_events) + 1,
            )
        )
        return False
    if applied:
        state.__dict__.update(staged_state.__dict__)
        verification_state.committed_candidate_ids.add(candidate.candidate_id)
        auto_apply_attempt = _lifecycle_attempt(
            audit_events, run_id, proposal.case_id, apply_action
        )
        audit_events.append(
            decision_audit_event(
                run_id=run_id,
                event_key=(
                    f"{resolution_action.lower()}-apply:{run_id}:{proposal.case_id}:"
                    f"{auto_apply_attempt}"
                ),
                timestamp=datetime.now(UTC),
                actor="system",
                action=apply_action,
                decision=resolution_action,
                verification_status="VERIFIED",
                financial_impact_paise=verification.financial_impact_paise,
                exception_id=proposal.case_id,
                evidence=_known_evidence(
                    proposal.evidence, verification_state.case_evidence, proposal.case_id
                ),
                before_state=before_state,
                after_state=_state_snapshot(state),
                lifecycle_order=len(audit_events) + 1,
            )
        )
    return applied


def _state_snapshot(state: ReconciliationState) -> dict[str, int]:
    return {
        "total_bank_credit_paise": state.total_bank_credit_paise,
        "explained_bank_credit_paise": state.explained_bank_credit_paise,
        "unexplained_residual_paise": state.unexplained_residual_paise,
    }


def _known_evidence(
    proposal_evidence: list[str], case_evidence: dict[str, set[str]], case_id: str
) -> list[str]:
    known_evidence = case_evidence.get(case_id, set())
    return [evidence for evidence in proposal_evidence if evidence in known_evidence]


def _proposal_impact_paise(
    proposal: AgentProposal, verification_state: ProposalVerificationState
) -> int:
    candidate = proposal.candidate_resolution
    if candidate is None:
        return 0
    candidates = verification_state.case_candidates.get(proposal.case_id, ())
    if not any(
        item.candidate_id == candidate.candidate_id and item.source_id == candidate.source_id
        for item in candidates
    ):
        return 0
    impact = verification_state.case_impacts_paise.get(proposal.case_id)
    return impact if type(impact) is int and impact >= 0 else 0


def _lifecycle_attempt(
    audit_events: list[AuditEvent], run_id: str, case_id: str, action: str
) -> int:
    return 1 + sum(
        event.run_id == run_id and event.exception_id == case_id and event.action == action
        for event in audit_events
    )
