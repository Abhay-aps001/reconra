from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from reconra.models.exception import BreakClass


@dataclass(frozen=True)
class ScenarioDistribution:
    scenario_counts: Mapping[BreakClass, int]
    base_record_count: int = 160

    def __post_init__(self) -> None:
        if type(self.base_record_count) is not int or self.base_record_count <= 0:
            raise ValueError("base_record_count must be a positive integer")
        normalized_counts: dict[BreakClass, int] = {}
        for break_class, count in self.scenario_counts.items():
            if not isinstance(break_class, BreakClass):
                raise TypeError("scenario_counts keys must be BreakClass values")
            if type(count) is not int or count <= 0:
                raise ValueError("scenario_counts values must be positive integers")
            normalized_counts[break_class] = count
        object.__setattr__(self, "scenario_counts", normalized_counts)
