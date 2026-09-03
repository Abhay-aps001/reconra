"""Truth-supplied scoring that keeps decision and bank-credit metrics separate."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields
from enum import StrEnum
from typing import Any

from reconra.models.exception import BreakClass, ResolutionStatus
from reconra.models.result import ReconciliationResult

Rate = tuple[int, int]


class DecisionOrigin(StrEnum):
    DETERMINISTIC = "DETERMINISTIC"
    AGENT = "AGENT"


@dataclass(frozen=True, slots=True)
class ExpectedDecision:
    record_id: str
    expected_candidate_id: str | None
    break_class: BreakClass
    resolvable: bool


@dataclass(frozen=True, slots=True)
class ObservedDecision:
    record_id: str
    candidate_id: str | None
    resolution_status: ResolutionStatus
    origin: DecisionOrigin = DecisionOrigin.DETERMINISTIC


@dataclass(frozen=True, slots=True)
class EvaluationReport:
    total_records: int
    resolved_records: int
    deterministic_resolved: int
    agent_assisted: int
    review_required: int
    escalated: int
    coverage: Rate | None
    auto_resolution_precision: Rate | None
    false_match_rate: Rate | None
    resolvable_record_recall: Rate | None
    correct_abstention_rate: Rate | None
    per_break_class_accuracy: dict[BreakClass, Rate] | None
    scoring_available: bool = False
    operational_outcome_count: int = 0
    ai_call_count: int = 0
    estimated_inference_cost_paise: int = 0
    total_bank_credit_paise: int = 0
    explained_bank_credit_paise: int = 0
    unexplained_residual_paise: int = 0
    elapsed_ns: int = 0
    records_per_second: Rate = (0, 1)

    def __post_init__(self) -> None:
        truth_metrics = (
            self.coverage,
            self.auto_resolution_precision,
            self.false_match_rate,
            self.resolvable_record_recall,
            self.correct_abstention_rate,
            self.per_break_class_accuracy,
        )
        if self.scoring_available and any(value is None for value in truth_metrics):
            raise ValueError("scored reports require all truth-derived metrics")
        if not self.scoring_available and any(value is not None for value in truth_metrics):
            raise ValueError("unscored reports must not contain truth-derived metrics")

    @classmethod
    def empty(cls, total_records: int = 0) -> EvaluationReport:
        _require_non_negative_int("total_records", total_records)
        return cls(
            total_records=total_records,
            resolved_records=0,
            deterministic_resolved=0,
            agent_assisted=0,
            review_required=0,
            escalated=0,
            coverage=None,
            auto_resolution_precision=None,
            false_match_rate=None,
            resolvable_record_recall=None,
            correct_abstention_rate=None,
            per_break_class_accuracy=None,
        )

    def has_binary_floats(self) -> bool:
        """Defensive check for artifact callers: finance/evaluation reports contain no float."""
        return _contains_float(self)

    def with_result(self, result: ReconciliationResult) -> EvaluationReport:
        """Add pipeline facts without turning unavailable truth metrics into scores.

        ``total_records`` is supplied by the caller as the number of canonical
        reconciliation rows, which is also the throughput unit. In an
        unscored report, payment matches resolve those source rows;
        settlement-to-bank matches and exceptions are separate cross-stage
        outcomes counted in ``operational_outcome_count``. A scored report
        retains its externally evaluated decision counts and receives only
        bank-credit facts here.
        """
        result_updates: dict[str, int] = {
            "total_bank_credit_paise": result.total_bank_credit_paise,
            "explained_bank_credit_paise": result.explained_bank_credit_paise,
            "unexplained_residual_paise": result.unexplained_residual_paise,
        }
        if not self.scoring_available:
            deterministic_resolved = len(result.payment_matches)
            result_updates.update(
                {
                    "resolved_records": deterministic_resolved,
                    "deterministic_resolved": deterministic_resolved,
                    "agent_assisted": 0,
                    "operational_outcome_count": (
                        deterministic_resolved
                        + len(result.settlement_bank_matches)
                        + len(result.exceptions)
                    ),
                    "review_required": sum(
                        exception.resolution_status is ResolutionStatus.REVIEW_REQUIRED
                        for exception in result.exceptions
                    ),
                    "escalated": sum(
                        exception.resolution_status is ResolutionStatus.ESCALATED
                        for exception in result.exceptions
                    ),
                }
            )
        return EvaluationReport(
            **{
                **{field.name: getattr(self, field.name) for field in fields(self)},
                **result_updates,
            }
        )


def evaluate_decisions(
    expected: Iterable[ExpectedDecision], observed: Iterable[ObservedDecision]
) -> EvaluationReport:
    """Score observed decisions against explicit external truth without inferring any match."""
    expected_by_id = _index_expected(expected)
    observed_by_id = _index_observed(observed, expected_by_id)

    total_records = len(expected_by_id)
    resolved_records = 0
    covered_records = 0
    deterministic_resolved = 0
    agent_assisted = 0
    review_required = 0
    escalated = 0
    correct_auto_matches = 0
    false_matches = 0
    correct_resolvable_matches = 0
    resolvable_count = 0
    correct_abstentions = 0
    abstention_count = 0
    class_correct: dict[BreakClass, int] = {}
    class_total: dict[BreakClass, int] = {}

    for record_id, expectation in expected_by_id.items():
        decision = observed_by_id.get(record_id)
        class_total[expectation.break_class] = class_total.get(expectation.break_class, 0) + 1
        if expectation.resolvable:
            resolvable_count += 1
        else:
            abstention_count += 1

        if decision is None:
            continue
        if decision.resolution_status is ResolutionStatus.REVIEW_REQUIRED:
            review_required += 1
        elif decision.resolution_status is ResolutionStatus.ESCALATED:
            escalated += 1

        is_correct_match = (
            expectation.expected_candidate_id is not None
            and decision.candidate_id == expectation.expected_candidate_id
        )
        is_correct_abstention = (
            expectation.expected_candidate_id is None and decision.candidate_id is None
        )
        is_auto = decision.resolution_status is ResolutionStatus.AUTO_RESOLVED
        if decision.candidate_id is not None:
            covered_records += 1
        if is_auto:
            resolved_records += 1
            if decision.origin is DecisionOrigin.DETERMINISTIC:
                deterministic_resolved += 1
            else:
                agent_assisted += 1
            if is_correct_match:
                correct_auto_matches += 1
                if expectation.resolvable:
                    correct_resolvable_matches += 1
            elif decision.candidate_id is not None:
                false_matches += 1

        if is_correct_abstention:
            correct_abstentions += 1
        if is_correct_match or is_correct_abstention:
            class_correct[expectation.break_class] = (
                class_correct.get(expectation.break_class, 0) + 1
            )

    return EvaluationReport(
        total_records=total_records,
        resolved_records=resolved_records,
        deterministic_resolved=deterministic_resolved,
        agent_assisted=agent_assisted,
        review_required=review_required,
        escalated=escalated,
        coverage=_rate(covered_records, total_records),
        auto_resolution_precision=_rate(correct_auto_matches, resolved_records),
        false_match_rate=_rate(false_matches, total_records),
        resolvable_record_recall=_rate(correct_resolvable_matches, resolvable_count),
        correct_abstention_rate=_rate(correct_abstentions, abstention_count),
        per_break_class_accuracy={
            break_class: _rate(class_correct.get(break_class, 0), count)
            for break_class, count in sorted(class_total.items(), key=lambda item: item[0].value)
        },
        scoring_available=True,
    )


def _index_expected(expected: Iterable[ExpectedDecision]) -> dict[str, ExpectedDecision]:
    result: dict[str, ExpectedDecision] = {}
    for decision in expected:
        if not isinstance(decision, ExpectedDecision):
            raise TypeError("expected decisions must be ExpectedDecision instances")
        _require_record_id(decision.record_id)
        if decision.record_id in result:
            raise ValueError(f"duplicate expected record_id: {decision.record_id}")
        result[decision.record_id] = decision
    return result


def _index_observed(
    observed: Iterable[ObservedDecision], expected: dict[str, ExpectedDecision]
) -> dict[str, ObservedDecision]:
    result: dict[str, ObservedDecision] = {}
    for decision in observed:
        if not isinstance(decision, ObservedDecision):
            raise TypeError("observed decisions must be ObservedDecision instances")
        _require_record_id(decision.record_id)
        if (
            decision.resolution_status is ResolutionStatus.AUTO_RESOLVED
            and decision.candidate_id is None
        ):
            raise ValueError("AUTO_RESOLVED requires a candidate_id")
        if decision.record_id not in expected:
            raise ValueError(f"observed record_id is absent from truth: {decision.record_id}")
        if decision.record_id in result:
            raise ValueError(f"duplicate observed record_id: {decision.record_id}")
        result[decision.record_id] = decision
    return result


def _rate(numerator: int, denominator: int) -> Rate:
    _require_non_negative_int("rate numerator", numerator)
    _require_non_negative_int("rate denominator", denominator)
    return numerator, denominator


def _require_record_id(value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("record_id must be a non-empty string")


def _require_non_negative_int(field_name: str, value: int) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")


def _contains_float(value: Any) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, tuple):
        return any(_contains_float(item) for item in value)
    if hasattr(value, "__dataclass_fields__"):
        return any(_contains_float(getattr(value, item.name)) for item in fields(value))
    return False
