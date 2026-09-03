"""Exact payment identity matching."""

from collections.abc import Sequence

from reconra.models.payment import Payment
from reconra.models.settlement import SettlementEntry
from reconra.normalization.ids import normalize_identifier
from reconra.reconciliation.state import MatchCandidate


def find_exact_payment_match(
    payment: Payment, entries: Sequence[SettlementEntry]
) -> MatchCandidate | None:
    """Return a single compatible exact payment-ID candidate, if one exists."""
    payment_id = normalize_identifier(payment.payment_id)
    if payment_id is None:
        return None

    compatible_entries = [
        entry
        for entry in entries
        if normalize_identifier(entry.payment_id) == payment_id
        and entry.amount_paise == payment.amount_paise
        and entry.currency == payment.currency
    ]
    if len(compatible_entries) != 1:
        return None

    return MatchCandidate(
        source_id=payment.payment_id,
        candidate_id=compatible_entries[0].entity_id,
        evidence=("payment_id", "amount_paise"),
    )
