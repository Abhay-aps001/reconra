"""Strict, non-authoritative schemas for residual-reasoning proposals."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator
from reconra.models.exception import BreakClass


class RecommendedAction(StrEnum):
    AUTO_RESOLVE = "AUTO_RESOLVE"
    REQUEST_REVIEW = "REQUEST_REVIEW"
    ESCALATE = "ESCALATE"
    ABSTAIN = "ABSTAIN"


class ReasoningAvailability(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class CandidateResolution(BaseModel):
    """An unverified candidate reference, not authorization to apply anything."""

    model_config = ConfigDict(strict=True, extra="forbid")

    source_id: str
    candidate_id: str


class AgentProposal(BaseModel):
    """A validated agent hypothesis subject to deterministic verification."""

    model_config = ConfigDict(strict=True, extra="forbid")

    case_id: str
    break_class: BreakClass
    hypothesis: str
    candidate_resolution: CandidateResolution | None
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str]
    recommended_action: RecommendedAction
    availability: ReasoningAvailability = ReasoningAvailability.AVAILABLE
    unavailable_reason: str | None = None

    @field_validator("break_class", mode="before")
    @classmethod
    def parse_break_class(cls, value: object) -> BreakClass:
        return value if isinstance(value, BreakClass) else BreakClass(value)  # type: ignore[arg-type]

    @field_validator("recommended_action", mode="before")
    @classmethod
    def parse_recommended_action(cls, value: object) -> RecommendedAction:
        return value if isinstance(value, RecommendedAction) else RecommendedAction(value)  # type: ignore[arg-type]
