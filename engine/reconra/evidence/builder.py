"""Build the sanitized, deterministic boundary for residual reasoning."""

from collections.abc import Iterable, Mapping
from datetime import date

from pydantic import BaseModel, ConfigDict, Field, StrictInt


class CandidateEvidence(BaseModel):
    """Already-computed facts about one candidate; never raw source content."""

    model_config = ConfigDict(strict=True, extra="forbid")

    source_id: str
    candidate_id: str
    amount_delta_paise: StrictInt
    date_delta_days: StrictInt
    utr_similarity: float | None = Field(default=None, ge=0.0, le=1.0)
    narration_similarity: float | None = Field(default=None, ge=0.0, le=1.0)
    exact_amount: bool
    normalized_similarity: float = Field(ge=0.0, le=1.0)
    evidence: tuple[str, ...]


class EvidencePacket(BaseModel):
    """Bounded facts a residual reasoner may inspect but never recalculate."""

    model_config = ConfigDict(strict=True, extra="forbid")

    case_id: str
    target_amount_paise: StrictInt
    target_date: date
    reference_fragments: tuple[str, ...]
    candidates: tuple[CandidateEvidence, ...]
    related_refund_count: StrictInt = Field(ge=0)
    related_adjustment_count: StrictInt = Field(ge=0)
    unresolved_reason: str


def build_evidence_packet(
    *,
    case_id: str,
    target_amount_paise: int,
    target_date: date,
    reference_fragments: tuple[str, ...],
    candidates: Iterable[CandidateEvidence | Mapping[str, object]],
    related_refund_count: int,
    related_adjustment_count: int,
    unresolved_reason: str,
) -> EvidencePacket:
    """Create an evidence packet from facts computed before agent invocation."""
    return EvidencePacket(
        case_id=case_id,
        target_amount_paise=target_amount_paise,
        target_date=target_date,
        reference_fragments=reference_fragments,
        candidates=tuple(
            candidate
            if isinstance(candidate, CandidateEvidence)
            else CandidateEvidence.model_validate(candidate)
            for candidate in candidates
        ),
        related_refund_count=related_refund_count,
        related_adjustment_count=related_adjustment_count,
        unresolved_reason=unresolved_reason,
    )
