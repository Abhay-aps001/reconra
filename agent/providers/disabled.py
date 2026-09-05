"""Safe typed fallback when a residual reasoning provider is unavailable."""

from reconra.evidence.builder import EvidencePacket
from reconra.models.exception import BreakClass

from agent.schemas.proposal import (
    AgentProposal,
    ReasoningAvailability,
    RecommendedAction,
)


class DisabledReasoner:
    """Return an explicit escalation proposal without making any financial claim."""

    async def reason(self, cases: list[EvidencePacket]) -> list[AgentProposal]:
        if cases:
            return [self._unavailable(case.case_id) for case in cases]
        return [self._unavailable("reasoner-unavailable")]

    @staticmethod
    def _unavailable(case_id: str) -> AgentProposal:
        return AgentProposal(
            case_id=case_id,
            break_class=BreakClass.UNRESOLVABLE,
            hypothesis="Residual reasoning provider is unavailable.",
            candidate_resolution=None,
            confidence=0.0,
            evidence=["reasoner:disabled"],
            recommended_action=RecommendedAction.ESCALATE,
            availability=ReasoningAvailability.UNAVAILABLE,
            unavailable_reason="DISABLED",
        )
