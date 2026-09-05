"""Risk gate for deterministic proposal verification results."""

from datetime import UTC, datetime

from reconra.audit.events import AuditEvent, decision_audit_event
from reconra.models.exception import BreakClass, ResolutionStatus
from reconra.policy.reconciliation import ReconciliationPolicy
from reconra.verification.verifier import VerificationResult

ResolutionDisposition = ResolutionStatus


def decide_resolution_action(
    proposal: object,
    verification: VerificationResult,
    policy: ReconciliationPolicy,
    *,
    run_id: str,
    audit_events: list[AuditEvent],
) -> ResolutionDisposition:
    """Decide only among auto, review, escalation, and rejection dispositions."""
    availability = getattr(proposal, "availability", "AVAILABLE")
    recommended_action = getattr(proposal, "recommended_action", None)
    break_class = getattr(proposal, "break_class", None)
    confidence = getattr(proposal, "confidence", None)
    if not verification.valid or str(availability) == "UNAVAILABLE":
        disposition = ResolutionDisposition.ESCALATED
    elif str(recommended_action) in {"ESCALATE", "ABSTAIN"}:
        disposition = ResolutionDisposition.ESCALATED
    elif str(recommended_action) == "REQUEST_REVIEW":
        disposition = ResolutionDisposition.REVIEW_REQUIRED
    elif break_class is BreakClass.UNRESOLVABLE:
        disposition = ResolutionDisposition.ESCALATED
    elif verification.financial_impact_paise > policy.high_impact_review_threshold_paise:
        disposition = ResolutionDisposition.REVIEW_REQUIRED
    elif not isinstance(confidence, float):
        disposition = ResolutionDisposition.ESCALATED
    elif confidence >= policy.auto_apply_confidence_threshold:
        disposition = ResolutionDisposition.AUTO_RESOLVED
    elif confidence >= policy.review_confidence_threshold:
        disposition = ResolutionDisposition.REVIEW_REQUIRED
    else:
        disposition = ResolutionDisposition.ESCALATED
    case_id = getattr(proposal, "case_id", None)
    audit_events.append(
        decision_audit_event(
            run_id=run_id,
            event_key=(
                f"risk:{run_id}:{case_id}:{disposition.value}:"
                f"{_lifecycle_attempt(audit_events, run_id, case_id)}"
            ),
            timestamp=datetime.now(UTC),
            actor="risk_gate",
            action="RISK_DISPOSITION",
            decision=disposition.value,
            verification_status="VERIFIED" if verification.valid else "FAILED",
            financial_impact_paise=verification.financial_impact_paise,
            exception_id=case_id if isinstance(case_id, str) else None,
            lifecycle_order=len(audit_events) + 1,
        )
    )
    return disposition


def _lifecycle_attempt(audit_events: list[AuditEvent], run_id: str, case_id: object) -> int:
    return 1 + sum(
        event.run_id == run_id
        and event.exception_id == case_id
        and event.action == "RISK_DISPOSITION"
        for event in audit_events
    )
