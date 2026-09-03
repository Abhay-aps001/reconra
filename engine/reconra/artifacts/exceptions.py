"""Export actionable exceptions without fabricating financial impact."""

from __future__ import annotations

import csv
from pathlib import Path

from reconra.models.result import ReconciliationResult

from .money import display_paise


def write_exception_worklist(result: ReconciliationResult, destination: Path) -> Path:
    """Write one stable row for every unresolved/reviewable reconciliation exception."""
    path = destination / "exception_worklist.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "exception_id",
                "break_class",
                "resolution_status",
                "financial_impact_paise",
                "financial_impact_display",
                "evidence",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        for exception in sorted(result.exceptions, key=lambda item: item.exception_id):
            writer.writerow(
                {
                    "exception_id": exception.exception_id,
                    "break_class": exception.break_class.value,
                    "resolution_status": exception.resolution_status.value,
                    "financial_impact_paise": exception.financial_impact_paise,
                    "financial_impact_display": display_paise(exception.financial_impact_paise),
                    "evidence": " | ".join(sorted(exception.evidence)),
                }
            )
    return path
