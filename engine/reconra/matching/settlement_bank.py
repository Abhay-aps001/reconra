"""Exact settlement-to-bank evidence matching."""

from collections.abc import Sequence
from datetime import date

from reconra.models.bank import BankTransaction
from reconra.normalization.dates import date_distance_days
from reconra.normalization.ids import normalize_utr
from reconra.reconciliation.state import MatchCandidate


def find_exact_bank_match(
    *,
    settlement_id: str,
    settlement_utr: str | None,
    expected_net_paise: int,
    settlement_date: date,
    bank_transactions: Sequence[BankTransaction],
    date_window_days: int,
) -> MatchCandidate | None:
    """Return a single exact UTR, amount, and date-compatible bank candidate."""
    if type(expected_net_paise) is not int:
        raise TypeError("expected_net_paise must be an integer paise value")
    if date_window_days < 0:
        raise ValueError("date_window_days must not be negative")

    settlement_utr_normalized = normalize_utr(settlement_utr)
    if settlement_utr_normalized is None:
        return None
    expected_credit_paise = max(expected_net_paise, 0)
    expected_debit_paise = max(-expected_net_paise, 0)

    compatible_transactions = [
        transaction
        for transaction in bank_transactions
        if normalize_utr(transaction.utr) == settlement_utr_normalized
        and transaction.credit_paise == expected_credit_paise
        and transaction.debit_paise == expected_debit_paise
        and date_distance_days(transaction.transaction_date, settlement_date) <= date_window_days
    ]
    if len(compatible_transactions) != 1:
        return None

    return MatchCandidate(
        source_id=settlement_id,
        candidate_id=compatible_transactions[0].bank_transaction_id,
        evidence=("settlement_utr", "credit_paise", "transaction_date"),
    )
