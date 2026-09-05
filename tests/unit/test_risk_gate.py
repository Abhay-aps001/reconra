from reconra.policy.reconciliation import ReconciliationPolicy
from reconra.verification import risk, verifier

from agent.schemas.proposal import AgentProposal


def test_high_financial_impact_requires_review_despite_high_confidence() -> None:
    """Fails if confidence alone can auto-apply a high-impact financial resolution."""
    proposal = AgentProposal(
        case_id="case-1",
        break_class="MANGLED_UTR",
        hypothesis="Reference format differs.",
        candidate_resolution={"source_id": "settlement-1", "candidate_id": "setl-1"},
        confidence=1.0,
        evidence=["normalized_utr_match"],
        recommended_action="AUTO_RESOLVE",
    )
    verification = verifier.VerificationResult(valid=True, reasons=(), financial_impact_paise=101)

    disposition = risk.decide_resolution_action(
        proposal,
        verification,
        ReconciliationPolicy(high_impact_review_threshold_paise=100),
        run_id="run-1",
        audit_events=[],
    )

    assert disposition.value == "REVIEW_REQUIRED"
