import pytest
from reconra.metrics.evaluator import (
    ExpectedDecision,
    ObservedDecision,
    evaluate_decisions,
)
from reconra.models.exception import BreakClass, ResolutionStatus


def test_evaluator_counts_a_wrong_auto_match_as_false_even_when_it_is_resolved() -> None:
    """A residual-reducing but incorrect candidate must never count as a correct match."""
    truth = [
        ExpectedDecision("record-clean", "candidate-clean", BreakClass.CLEAN_MATCH, True),
        ExpectedDecision("record-review", None, BreakClass.UNRESOLVABLE, False),
        ExpectedDecision("record-wrong", "candidate-right", BreakClass.MANGLED_UTR, True),
    ]
    observed = [
        ObservedDecision("record-clean", "candidate-clean", ResolutionStatus.AUTO_RESOLVED),
        ObservedDecision("record-review", None, ResolutionStatus.ESCALATED),
        ObservedDecision("record-wrong", "candidate-wrong", ResolutionStatus.AUTO_RESOLVED),
    ]

    report = evaluate_decisions(truth, observed)

    assert report.total_records == 3
    assert report.resolved_records == 2
    assert report.auto_resolution_precision == (1, 2)
    assert report.false_match_rate == (1, 3)
    assert report.resolvable_record_recall == (1, 2)
    assert report.correct_abstention_rate == (1, 1)
    assert report.per_break_class_accuracy[BreakClass.MANGLED_UTR] == (0, 1)


def test_evaluator_counts_review_and_escalation_without_binary_float_rates() -> None:
    truth = [
        ExpectedDecision("record-a", "candidate-a", BreakClass.CLEAN_MATCH, True),
        ExpectedDecision("record-b", None, BreakClass.UNRESOLVABLE, False),
    ]
    observed = [
        ObservedDecision("record-a", "candidate-a", ResolutionStatus.REVIEW_REQUIRED),
        ObservedDecision("record-b", None, ResolutionStatus.ESCALATED),
    ]

    report = evaluate_decisions(truth, observed)

    assert report.review_required == 1
    assert report.escalated == 1
    assert report.coverage == (1, 2)
    assert report.has_binary_floats() is False


def test_evaluator_rejects_auto_resolution_without_a_candidate() -> None:
    truth = [ExpectedDecision("record-a", None, BreakClass.UNRESOLVABLE, False)]
    observed = [ObservedDecision("record-a", None, ResolutionStatus.AUTO_RESOLVED)]

    with pytest.raises(ValueError, match="AUTO_RESOLVED requires a candidate_id"):
        evaluate_decisions(truth, observed)
