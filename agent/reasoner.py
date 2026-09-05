"""Provider-neutral residual reasoning contract."""

from typing import Protocol

from reconra.evidence.builder import EvidencePacket

from agent.schemas.proposal import AgentProposal


class ResidualReasoner(Protocol):
    async def reason(self, cases: list[EvidencePacket]) -> list[AgentProposal]: ...
