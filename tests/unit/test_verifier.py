from reconra.evidence.builder import CandidateEvidence
from reconra.policy.reconciliation import ReconciliationPolicy
from reconra.verification import verifier

from agent.schemas.proposal import AgentProposal


def _candidate() -> CandidateEvidence:
    return CandidateEvidence(
        source_id="setl-1", candidate_id="bank-1", amount_delta_paise=0, date_delta_days=0,
        utr_similarity=0.95, narration_similarity=None, exact_amount=True,
        normalized_similarity=0.95,
        evidence=("fuzzy_utr", "exact_amount", "date_within_policy_window"),
    )


def _proposal(**updates: object) -> AgentProposal:
    values: dict[str, object] = {
        "case_id": "case-1", "break_class": "MANGLED_UTR", "hypothesis": "Reference differs.",
        "candidate_resolution": {"source_id": "setl-1", "candidate_id": "bank-1"},
        "confidence": 0.99, "evidence": ["fuzzy_utr"], "recommended_action": "AUTO_RESOLVE",
    }
    values.update(updates)
    return AgentProposal(**values)


def _state(*, committed: set[str] | None = None) -> verifier.ProposalVerificationState:
    return verifier.ProposalVerificationState(
        case_evidence={"case-1": {"fuzzy_utr"}}, case_candidates={"case-1": (_candidate(),)},
        case_impacts_paise={"case-1": 100}, available_unexplained_paise=100,
        committed_candidate_ids=committed or set(),
    )


def test_verifier_rejects_fabricated_evidence() -> None:
    result = verifier.verify_proposal(
        _proposal(evidence=["invented_evidence"]), _state(), ReconciliationPolicy(),
        run_id="run-1", audit_events=[],
    )

    assert result.valid is False
    assert "EVIDENCE_NOT_PRESENT" in result.reasons


def test_verifier_rejects_committed_candidate_reuse() -> None:
    result = verifier.verify_proposal(
        _proposal(), _state(committed={"bank-1"}), ReconciliationPolicy(),
        run_id="run-1", audit_events=[],
    )

    assert result.valid is False
    assert "CANDIDATE_ALREADY_COMMITTED" in result.reasons
