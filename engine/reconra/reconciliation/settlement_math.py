"""Deterministic settlement arithmetic."""

from collections.abc import Sequence

from reconra.models.settlement import SettlementEntry


def recompute_settlement_net(entries: Sequence[SettlementEntry]) -> int:
    """Recompute a settlement's net amount from its component entries."""
    return sum(
        entry.credit_paise - entry.debit_paise - entry.fee_paise - entry.tax_paise
        for entry in entries
    )
