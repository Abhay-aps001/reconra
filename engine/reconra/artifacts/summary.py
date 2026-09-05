"""Export run and evaluation metrics without serializing binary floating-point values."""

from __future__ import annotations

from dataclasses import fields
from json import dumps
from pathlib import Path
from typing import Any

from reconra.metrics.evaluator import EvaluationReport
from reconra.models.result import ReconciliationResult

from .money import display_paise


def write_reconciliation_summary(
    result: ReconciliationResult, metrics: EvaluationReport, destination: Path
) -> Path:
    """Write a deterministic summary with exact count/rate and paise fields."""
    if metrics.has_binary_floats():
        raise ValueError("summary metrics must not contain binary floating-point values")
    path = destination / "reconciliation_summary.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "run_id": result.run_id,
        "completed": result.completed,
        "bank_credit": {
            "total_paise": result.total_bank_credit_paise,
            "explained_paise": result.explained_bank_credit_paise,
            "residual_paise": result.unexplained_residual_paise,
            "total_display": display_paise(result.total_bank_credit_paise),
            "explained_display": display_paise(result.explained_bank_credit_paise),
            "residual_display": display_paise(result.unexplained_residual_paise),
        },
        "metrics": _summary_metrics(metrics.with_result(result)),
    }
    path.write_text(
        dumps(summary, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return path


def _summary_metrics(report: EvaluationReport) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for field in fields(report):
        value = getattr(report, field.name)
        if field.name == "per_break_class_accuracy":
            result[field.name] = (
                {
                    break_class.value: _rate_payload(rate)
                    for break_class, rate in sorted(value.items(), key=lambda item: item[0].value)
                }
                if value is not None
                else None
            )
        elif _is_rate(value):
            result[field.name] = _rate_payload(value)
        else:
            result[field.name] = value
    return result


def _is_rate(value: object) -> bool:
    return isinstance(value, tuple) and len(value) == 2 and all(type(item) is int for item in value)


def _rate_payload(rate: tuple[int, int]) -> dict[str, int]:
    return {"numerator": rate[0], "denominator": rate[1]}
