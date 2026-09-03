from pydantic import Field

from reconra.audit.events import AuditEvent

from .base import CanonicalModel, PaiseField
from .exception import ReconciliationException


class DeterministicMatch(CanonicalModel):
    """A verified deterministic linkage without any state-mutating AI decision."""

    source_id: str
    candidate_id: str
    evidence: list[str] = Field(default_factory=list)
    financial_impact_paise: PaiseField = 0


class ReconciliationResult(CanonicalModel):
    run_id: str
    total_bank_credit_paise: PaiseField
    explained_bank_credit_paise: PaiseField
    unexplained_residual_paise: PaiseField
    exceptions: list[ReconciliationException] = Field(default_factory=list)
    payment_matches: list[DeterministicMatch] = Field(default_factory=list)
    settlement_bank_matches: list[DeterministicMatch] = Field(default_factory=list)
    stages: list[str] = Field(default_factory=list)
    audit_events: list[AuditEvent] = Field(default_factory=list)
    completed: bool = False
