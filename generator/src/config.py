from __future__ import annotations

from enum import StrEnum


class DatasetRole(StrEnum):
    CLEAN = "clean"
    MESSY_DEV = "messy-dev"
    DEMO = "demo"
    HELDOUT = "heldout"
    STRESS = "stress"


DATASET_SEEDS: dict[DatasetRole, int] = {
    DatasetRole.CLEAN: 1101,
    DatasetRole.MESSY_DEV: 2202,
    DatasetRole.DEMO: 3303,
    DatasetRole.HELDOUT: 4404,
    DatasetRole.STRESS: 5505,
}

MESSY_DEV_BASE_RECORD_COUNT = 160
DEMO_BASE_RECORD_COUNT = 244
HELDOUT_BASE_RECORD_COUNT = 180
STRESS_BASE_RECORD_COUNT = 10_000
