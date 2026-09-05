"""Structured, deterministic decision-audit events."""

from datetime import datetime
from hashlib import sha256

from pydantic import Field
from reconra.models.base import CanonicalModel, PaiseField


class AuditEvent(CanonicalModel):
    """A financial decision record, distinct from a technical log entry."""

    event_id: str
    run_id: str
    timestamp: datetime
    actor: str
    action: str
    decision: str
    verification_status: str
    financial_impact_paise: PaiseField
    exception_id: str | None = None
    evidence: list[str] = Field(default_factory=list)
    before_state: dict[str, int] = Field(default_factory=dict)
    after_state: dict[str, int] = Field(default_factory=dict)
    lifecycle_order: int = Field(default=0, ge=0)


def decision_audit_event(
    *,
    run_id: str,
    event_key: str,
    timestamp: datetime,
    actor: str,
    action: str,
    decision: str,
    verification_status: str,
    financial_impact_paise: int,
    exception_id: str | None = None,
    evidence: list[str] | None = None,
    before_state: dict[str, int] | None = None,
    after_state: dict[str, int] | None = None,
    lifecycle_order: int = 0,
) -> AuditEvent:
    """Create a complete, stable decision audit event without technical-log side effects."""
    return AuditEvent(
        event_id=(
            f"event_{sha256(f'{run_id}:{event_key}'.encode()).hexdigest()[:20]}"
        ),
        run_id=run_id,
        timestamp=timestamp,
        actor=actor,
        action=action,
        decision=decision,
        verification_status=verification_status,
        financial_impact_paise=financial_impact_paise,
        exception_id=exception_id,
        evidence=evidence or [],
        before_state=before_state or {},
        after_state=after_state or {},
        lifecycle_order=lifecycle_order,
    )
