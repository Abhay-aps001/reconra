from __future__ import annotations

from json import dumps
from pathlib import Path
from typing import Any

from .clean import GeneratedDataset

_RAW_SOURCE_NAMES = ("orders", "payments", "reconciliation_rows", "bank_transactions")


def _reject_float_and_truth_fields(value: Any) -> None:
    if isinstance(value, float):
        raise TypeError("generated artifacts cannot contain binary floating-point values")
    if isinstance(value, dict):
        for field_name, nested_value in value.items():
            lowered_name = str(field_name).lower()
            if any(
                fragment in lowered_name
                for fragment in ("truth", "expected", "resolvable", "answer")
            ):
                raise ValueError("raw artifact contains a ground-truth field")
            _reject_float_and_truth_fields(nested_value)
    elif isinstance(value, list):
        for nested_value in value:
            _reject_float_and_truth_fields(nested_value)


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_dataset_artifacts(dataset: GeneratedDataset, output_directory: Path) -> dict[str, Path]:
    output_directory.mkdir(parents=True, exist_ok=True)
    output_paths: dict[str, Path] = {}
    for source_name in _RAW_SOURCE_NAMES:
        raw_records = dataset.raw_inputs[source_name]
        _reject_float_and_truth_fields(raw_records)
        path = output_directory / f"{source_name}.json"
        _write_json(path, raw_records)
        output_paths[source_name] = path

    ground_truth_path = output_directory / "ground_truth.json"
    _write_json(ground_truth_path, dataset.ground_truth or {"cases": []})
    output_paths["ground_truth"] = ground_truth_path
    return output_paths
