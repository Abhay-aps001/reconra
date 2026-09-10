"""Publish and validate an honest, static saved benchmark fallback."""

from __future__ import annotations

import argparse
from json import JSONDecodeError, dumps, loads
from pathlib import Path
from typing import Any, cast

PROJECT_ROOT = Path(__file__).resolve().parents[1]
_REQUIRED_INT_FIELDS = (
    "total_records",
    "resolved_records",
    "deterministic_resolved",
    "agent_assisted",
    "review_required",
    "escalated",
    "operational_outcome_count",
    "total_bank_credit_paise",
    "explained_bank_credit_paise",
    "unexplained_residual_paise",
)
_TRUTH_METRICS = {
    "accuracy",
    "precision",
    "recall",
    "f1",
    "coverage",
    "auto_resolution_precision",
    "auto_resolution_rate",
    "false_match_rate",
    "resolvable_record_recall",
    "correct_abstention_rate",
    "per_break_class_accuracy",
}


def build_saved_benchmark(source: dict[str, Any]) -> dict[str, Any]:
    """Keep only stable, public facts from an unscored benchmark output."""
    if source.get("scoring_available") is not False:
        raise ValueError("a saved fallback requires an explicitly unscored benchmark")
    provider_status = source.get("agent_provider_status")
    if provider_status is None and source.get("mode") == "deterministic":
        provider_status = "NOT_APPLICABLE"
    if not isinstance(provider_status, str):
        raise ValueError("benchmark source is missing its provider execution status")

    payload: dict[str, Any] = {
        "schema_version": 1,
        "artifact_type": "SAVED_BENCHMARK_RESULT",
        "dataset": source["dataset"],
        "mode": source["mode"],
        "agent_provider_status": provider_status,
        "scoring_available": False,
        "scoring_unavailable_reason": source["scoring_unavailable_reason"],
        "note": (
            "Saved benchmark evidence from a deliberate local evaluation run. "
            "It is not a live benchmark and contains no truth-derived score."
        ),
    }
    for field in _REQUIRED_INT_FIELDS:
        payload[field] = source[field]
    if not _is_valid_saved_benchmark(payload):
        raise ValueError("benchmark source does not satisfy the saved fallback contract")
    return payload


def load_saved_benchmark(path: Path) -> dict[str, Any] | None:
    """Return a valid saved result or None; an unavailable fallback is never an error."""
    try:
        payload = loads(path.read_text(encoding="utf-8"))
    except (OSError, JSONDecodeError):
        return None
    return payload if _is_valid_saved_benchmark(payload) else None


def _is_valid_saved_benchmark(payload: object) -> bool:
    if not isinstance(payload, dict):
        return False
    if payload.get("schema_version") != 1:
        return False
    if payload.get("artifact_type") != "SAVED_BENCHMARK_RESULT":
        return False
    if payload.get("scoring_available") is not False:
        return False
    if not isinstance(payload.get("dataset"), str) or not isinstance(payload.get("mode"), str):
        return False
    if not isinstance(payload.get("scoring_unavailable_reason"), str):
        return False
    if _TRUTH_METRICS.intersection(payload):
        return False
    if any(
        type(payload.get(field)) is not int or payload[field] < 0
        for field in _REQUIRED_INT_FIELDS
    ):
        return False
    total_bank_credit_paise = cast(int, payload["total_bank_credit_paise"])
    explained_bank_credit_paise = cast(int, payload["explained_bank_credit_paise"])
    unexplained_residual_paise = cast(int, payload["unexplained_residual_paise"])
    return total_bank_credit_paise == explained_bank_credit_paise + unexplained_residual_paise


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish Reconra's saved benchmark fallback.")
    parser.add_argument(
        "--input",
        type=Path,
        default=PROJECT_ROOT / "docs" / "evaluation" / "heldout-deterministic" / "benchmark.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "docs" / "evaluation" / "saved-benchmark.json",
    )
    args = parser.parse_args()
    source = loads(args.input.read_text(encoding="utf-8"))
    saved = build_saved_benchmark(source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(dumps(saved, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
