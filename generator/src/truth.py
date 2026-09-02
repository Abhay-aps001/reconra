from __future__ import annotations

from typing import Any

from reconra.models.exception import BreakClass


def create_ground_truth_case(
    case_id: str, break_class: BreakClass, raw_entity_ids: list[str]
) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "break_class": break_class.value,
        "raw_entity_ids": raw_entity_ids,
    }


def create_ground_truth(cases: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    return {"cases": cases}
