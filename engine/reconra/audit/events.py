"""Structured, deterministic decision-audit events."""

from datetime import datetime

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
