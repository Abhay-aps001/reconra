"""Export verified deterministic matches as a stable reconciled ledger."""

from __future__ import annotations

import csv
from pathlib import Path

from reconra.models.result import DeterministicMatch, ReconciliationResult

from .money import display_paise


def write_reconciled_ledger(result: ReconciliationResult, destination: Path) -> Path:
    """Write the actual match decisions in a deterministic, paise-preserving CSV."""
    path = destination / "reconciled_ledger.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [_ledger_row("payment", match) for match in result.payment_matches] + [
        _ledger_row("settlement_bank", match) for match in result.settlement_bank_matches
    ]
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "record_type",
                "source_id",
                "candidate_id",
                "financial_impact_paise",
                "financial_impact_display",
                "evidence",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda row: (row["record_type"], row["source_id"])))
    return path


def _ledger_row(record_type: str, match: DeterministicMatch) -> dict[str, str | int]:
    return {
        "record_type": record_type,
        "source_id": match.source_id,
        "candidate_id": match.candidate_id,
        "financial_impact_paise": match.financial_impact_paise,
        "financial_impact_display": display_paise(match.financial_impact_paise),
        "evidence": " | ".join(sorted(match.evidence)),
    }
