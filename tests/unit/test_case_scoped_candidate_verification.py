from reconra.evidence.builder import CandidateEvidence
from reconra.policy.reconciliation import ReconciliationPolicy
from reconra.verification.verifier import ProposalVerificationState, verify_proposal

from agent.schemas.proposal import AgentProposal


def _candidate(**updates: object) -> CandidateEvidence:
    values: dict[str, object] = {
        "source_id": "settlement-a",
        "candidate_id": "bank-1",
        "amount_delta_paise": 0,
        "date_delta_days": 1,
        "utr_similarity": 0.95,
        "narration_similarity": 0.25,
        "exact_amount": True,
        "normalized_similarity": 0.95,
        "evidence": ("fuzzy_utr", "exact_amount", "date_within_policy_window"),
    }
    values.update(updates)
    return CandidateEvidence(**values)


def _proposal(case_id: str, **updates: object) -> AgentProposal:
    values: dict[str, object] = {
        "case_id": case_id,
        "break_class": "MANGLED_UTR",
        "hypothesis": "The normalized reference differs.",
        "candidate_resolution": {"candidate_id": "bank-1", "source_id": "settlement-a"},
        "confidence": 1.0,
        "evidence": ["fuzzy_utr"],
        "recommended_action": "AUTO_RESOLVE",
    }
    values.update(updates)
    return AgentProposal(**values)


def _state(
    candidates_by_case: dict[str, tuple[CandidateEvidence, ...]],
    *,
    committed: set[str] | None = None,
) -> ProposalVerificationState:
    return ProposalVerificationState(
        case_evidence={
            case_id: {evidence for candidate in candidates for evidence in candidate.evidence}
            for case_id, candidates in candidates_by_case.items()
        },
        case_candidates=candidates_by_case,
        case_impacts_paise={case_id: 100 for case_id in candidates_by_case},
        available_unexplained_paise=100,
        committed_candidate_ids=committed or set(),
    )


def test_candidate_discovered_for_another_residual_is_rejected() -> None:
    """A globally known bank transaction cannot authorize a different residual."""
    state = _state({"residual-a": (_candidate(),), "residual-b": ()})

    result = verify_proposal(
        _proposal("residual-b"),
        state,
        ReconciliationPolicy(high_impact_review_threshold_paise=100),
        run_id="run-1",
        audit_events=[],
    )

    assert result.valid is False
    assert "CANDIDATE_NOT_FOUND_FOR_CASE" in result.reasons


def test_case_scoped_candidate_with_matching_facts_is_accepted() -> None:
    result = verify_proposal(
        _proposal("residual-a"),
        _state({"residual-a": (_candidate(),)}),
        ReconciliationPolicy(high_impact_review_threshold_paise=100),
        run_id="run-1",
        audit_events=[],
    )

    assert result.valid is True
    assert result.financial_impact_paise == 100


def test_candidate_source_id_mismatch_is_rejected() -> None:
    result = verify_proposal(
        _proposal(
            "residual-a",
            candidate_resolution={"candidate_id": "bank-1", "source_id": "other"},
        ),
        _state({"residual-a": (_candidate(),)}),
        ReconciliationPolicy(high_impact_review_threshold_paise=100),
        run_id="run-1",
        audit_events=[],
    )

    assert result.valid is False
    assert "CANDIDATE_SOURCE_MISMATCH" in result.reasons


def test_amount_incompatible_candidate_is_rejected() -> None:
    result = verify_proposal(
        _proposal("residual-a"),
        _state({"residual-a": (_candidate(amount_delta_paise=1, exact_amount=False),)}),
        ReconciliationPolicy(rounding_tolerance_paise=0, high_impact_review_threshold_paise=100),
        run_id="run-1",
        audit_events=[],
    )

    assert result.valid is False
    assert "CANDIDATE_AMOUNT_INCOMPATIBLE" in result.reasons


def test_date_incompatible_candidate_is_rejected() -> None:
    result = verify_proposal(
        _proposal("residual-a"),
        _state({"residual-a": (_candidate(date_delta_days=3),)}),
        ReconciliationPolicy(settlement_date_window_days=2, high_impact_review_threshold_paise=100),
        run_id="run-1",
        audit_events=[],
    )

    assert result.valid is False
    assert "CANDIDATE_DATE_INCOMPATIBLE" in result.reasons


def test_break_class_incompatible_with_candidate_evidence_is_rejected() -> None:
    result = verify_proposal(
        _proposal("residual-a", break_class="MANGLED_NARRATION"),
        _state({"residual-a": (_candidate(),)}),
        ReconciliationPolicy(high_impact_review_threshold_paise=100),
        run_id="run-1",
        audit_events=[],
    )

    assert result.valid is False
    assert "BREAK_CLASS_INCOMPATIBLE" in result.reasons


def test_consumed_candidate_is_rejected() -> None:
    result = verify_proposal(
        _proposal("residual-a"),
        _state({"residual-a": (_candidate(),)}, committed={"bank-1"}),
        ReconciliationPolicy(high_impact_review_threshold_paise=100),
        run_id="run-1",
        audit_events=[],
    )

    assert result.valid is False
    assert "CANDIDATE_ALREADY_COMMITTED" in result.reasons
