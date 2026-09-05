import asyncio

import pytest
from pydantic import ValidationError

from agent.providers import disabled
from agent.schemas import proposal


def test_agent_proposal_rejects_unknown_break_class() -> None:
    """Fails if free-form agent classifications bypass the closed finance taxonomy."""
    with pytest.raises(ValidationError) as error:
        proposal.AgentProposal(
            case_id="case-1",
            break_class="INVENTED_CLASS",
            hypothesis="The reference may be mangled.",
            candidate_resolution={"source_id": "settlement-1", "candidate_id": "setl-1"},
            confidence=0.8,
            evidence=["normalized_utr_match"],
            recommended_action="REQUEST_REVIEW",
        )
    assert any(item["loc"] == ("break_class",) for item in error.value.errors())


@pytest.mark.parametrize("confidence", [-0.01, 1.01])
def test_agent_proposal_rejects_confidence_outside_unit_interval(confidence: float) -> None:
    """Fails if an agent can overstate certainty outside the approved range."""
    with pytest.raises(ValidationError) as error:
        proposal.AgentProposal(
            case_id="case-1",
            break_class="MANGLED_UTR",
            hypothesis="The reference may be mangled.",
            candidate_resolution={"source_id": "settlement-1", "candidate_id": "setl-1"},
            confidence=confidence,
            evidence=["normalized_utr_match"],
            recommended_action="REQUEST_REVIEW",
        )
    assert any(item["loc"] == ("confidence",) for item in error.value.errors())


def test_agent_proposal_rejects_malformed_recommended_action() -> None:
    """Fails if unsupported actions can enter the deterministic verifier."""
    with pytest.raises(ValidationError) as error:
        proposal.AgentProposal(
            case_id="case-1",
            break_class="MANGLED_UTR",
            hypothesis="The reference may be mangled.",
            candidate_resolution={"source_id": "settlement-1", "candidate_id": "setl-1"},
            confidence=0.8,
            evidence=["normalized_utr_match"],
            recommended_action="APPLY_MONEY_DIRECTLY",
        )
    assert any(item["loc"] == ("recommended_action",) for item in error.value.errors())


def test_disabled_reasoner_returns_typed_unavailable_proposal() -> None:
    """Fails if disabled mode forces callers to parse an untyped provider failure."""
    results = asyncio.run(disabled.DisabledReasoner().reason([]))

    assert len(results) == 1
    assert results[0].availability is proposal.ReasoningAvailability.UNAVAILABLE
    assert results[0].recommended_action is proposal.RecommendedAction.ESCALATE
