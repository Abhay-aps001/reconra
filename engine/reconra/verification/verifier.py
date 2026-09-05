"""Deterministic verification of non-authoritative agent proposals."""

from dataclasses import dataclass, field
from datetime import UTC, datetime

from reconra.audit.events import AuditEvent, decision_audit_event
from reconra.evidence.builder import CandidateEvidence
from reconra.models.exception import BreakClass
from reconra.policy.reconciliation import ReconciliationPolicy


@dataclass(slots=True)
class ProposalVerificationState:
    """Case-scoped facts from the current run that a proposal must prove against."""

    case_evidence: dict[str, set[str]]
    case_candidates: dict[str, tuple[CandidateEvidence, ...]]
    case_impacts_paise: dict[str, int]
    available_unexplained_paise: int
    committed_candidate_ids: set[str] = field(default_factory=set)


@dataclass(frozen=True, slots=True)
class VerificationResult:
    valid: bool
    reasons: tuple[str, ...]
    financial_impact_paise: int = 0


def verify_proposal(
    proposal: object,
    state: ProposalVerificationState,
    policy: ReconciliationPolicy,
    *,
    run_id: str,
    audit_events: list[AuditEvent],
) -> VerificationResult:
    """Prove a proposal against only candidates discovered for its exact case."""
    reasons: list[str] = []
    case_id = getattr(proposal, "case_id", None)
    proposal_evidence = getattr(proposal, "evidence", ())
    candidate = getattr(proposal, "candidate_resolution", None)
    known_evidence: set[str] = set()
    if not isinstance(case_id, str) or not isinstance(proposal_evidence, list):
        reasons.append("PROPOSAL_INVALID")
    else:
        known_evidence = state.case_evidence.get(case_id, set())
        if case_id not in state.case_evidence:
            reasons.append("CASE_NOT_FOUND")
        elif not set(proposal_evidence).issubset(known_evidence):
            reasons.append("EVIDENCE_NOT_PRESENT")

    candidate_id = getattr(candidate, "candidate_id", None)
    source_id = getattr(candidate, "source_id", None)
    candidate_key = "missing"
    impact = 0
    discovered: CandidateEvidence | None = None
    if not isinstance(candidate_id, str) or not isinstance(source_id, str):
        reasons.append("CANDIDATE_NOT_PRESENT")
    else:
        candidate_key = f"{source_id}:{candidate_id}"
        case_candidates = state.case_candidates.get(case_id, ()) if isinstance(case_id, str) else ()
        matching_id = [item for item in case_candidates if item.candidate_id == candidate_id]
        discovered = next((item for item in matching_id if item.source_id == source_id), None)
        if discovered is None:
            reasons.append(
                "CANDIDATE_SOURCE_MISMATCH" if matching_id else "CANDIDATE_NOT_FOUND_FOR_CASE"
            )
        if candidate_id in state.committed_candidate_ids:
            reasons.append("CANDIDATE_ALREADY_COMMITTED")

    if discovered is not None:
        if (
            discovered.amount_delta_paise > policy.rounding_tolerance_paise
            or discovered.exact_amount != (discovered.amount_delta_paise == 0)
        ):
            reasons.append("CANDIDATE_AMOUNT_INCOMPATIBLE")
        if discovered.date_delta_days > policy.settlement_date_window_days:
            reasons.append("CANDIDATE_DATE_INCOMPATIBLE")
        if not _break_class_supported(getattr(proposal, "break_class", None), discovered):
            reasons.append("BREAK_CLASS_INCOMPATIBLE")
        candidate_impact = (
            state.case_impacts_paise.get(case_id) if isinstance(case_id, str) else None
        )
        if type(candidate_impact) is not int or candidate_impact < 0:
            reasons.append("CANDIDATE_IMPACT_INVALID")
        elif candidate_impact > state.available_unexplained_paise:
            reasons.append("CONSERVATION_IMPOSSIBLE")
        else:
            impact = candidate_impact

    result = VerificationResult(not reasons, tuple(reasons), impact)
    decision = "VERIFIED" if result.valid else f"REJECTED:{','.join(result.reasons)}"
    audit_events.append(
        decision_audit_event(
            run_id=run_id,
            event_key=(
                f"verification:{run_id}:{case_id}:{candidate_key}:"
                f"{_lifecycle_attempt(audit_events, run_id, case_id, 'VERIFY_PROPOSAL')}"
            ),
            timestamp=datetime.now(UTC),
            actor="verifier",
            action="VERIFY_PROPOSAL",
            decision=decision,
            verification_status="VERIFIED" if result.valid else "FAILED",
            financial_impact_paise=result.financial_impact_paise,
            exception_id=case_id if isinstance(case_id, str) else None,
            evidence=(
                [evidence for evidence in proposal_evidence if evidence in known_evidence]
                if isinstance(proposal_evidence, list)
                else []
            ),
            lifecycle_order=len(audit_events) + 1,
        )
    )
    return result


def _break_class_supported(break_class: object, candidate: CandidateEvidence) -> bool:
    if break_class is BreakClass.MANGLED_UTR:
        return "fuzzy_utr" in candidate.evidence
    if break_class is BreakClass.MANGLED_NARRATION:
        return "fuzzy_narration" in candidate.evidence
    if break_class is BreakClass.ROUNDING_VARIANCE:
        return "rounding_tolerance" in candidate.evidence
    return False


def _lifecycle_attempt(
    audit_events: list[AuditEvent], run_id: str, case_id: object, action: str
) -> int:
    return 1 + sum(
        event.run_id == run_id and event.exception_id == case_id and event.action == action
        for event in audit_events
    )
