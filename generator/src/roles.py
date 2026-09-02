from __future__ import annotations

from reconra.models.exception import BreakClass

from generator.scenarios.distribution import ScenarioDistribution

from .clean import GeneratedDataset, generate_clean_dataset
from .config import (
    DATASET_SEEDS,
    DEMO_BASE_RECORD_COUNT,
    HELDOUT_BASE_RECORD_COUNT,
    MESSY_DEV_BASE_RECORD_COUNT,
    STRESS_BASE_RECORD_COUNT,
    DatasetRole,
)
from .messy import generate_messy_dataset

NON_CLEAN_BREAK_CLASSES = tuple(
    break_class for break_class in BreakClass if break_class is not BreakClass.CLEAN_MATCH
)


def _full_coverage_profile(base_record_count: int) -> ScenarioDistribution:
    return ScenarioDistribution(
        scenario_counts={break_class: 1 for break_class in NON_CLEAN_BREAK_CLASSES},
        base_record_count=base_record_count,
    )


def _demo_profile() -> ScenarioDistribution:
    return ScenarioDistribution(
        scenario_counts={
            BreakClass.MANGLED_NARRATION: 1,
            BreakClass.MANGLED_UTR: 1,
            BreakClass.PARTIAL_REFUND: 1,
            BreakClass.UNRESOLVABLE: 1,
        },
        base_record_count=DEMO_BASE_RECORD_COUNT,
    )


def generate_dataset(role: DatasetRole) -> GeneratedDataset:
    if role is DatasetRole.CLEAN:
        return generate_clean_dataset(seed=DATASET_SEEDS[role])
    if role is DatasetRole.MESSY_DEV:
        return generate_messy_dataset(
            seed=DATASET_SEEDS[role], profile=_full_coverage_profile(MESSY_DEV_BASE_RECORD_COUNT)
        )
    if role is DatasetRole.DEMO:
        return generate_messy_dataset(seed=DATASET_SEEDS[role], profile=_demo_profile())
    if role is DatasetRole.HELDOUT:
        return generate_messy_dataset(
            seed=DATASET_SEEDS[role], profile=_full_coverage_profile(HELDOUT_BASE_RECORD_COUNT)
        )
    if role is DatasetRole.STRESS:
        return generate_messy_dataset(
            seed=DATASET_SEEDS[role],
            profile=ScenarioDistribution(
                scenario_counts={}, base_record_count=STRESS_BASE_RECORD_COUNT
            ),
        )
    raise ValueError(f"unsupported dataset role: {role}")
