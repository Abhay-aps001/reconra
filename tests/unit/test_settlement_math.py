from datetime import datetime

from reconra.models.settlement import SettlementEntry
from reconra.reconciliation.settlement_math import recompute_settlement_net


def settlement_entry(
    entity_id: str,
    *,
    credit_paise: int = 0,
    debit_paise: int = 0,
    fee_paise: int = 0,
    tax_paise: int = 0,
) -> SettlementEntry:
    return SettlementEntry(
        entity_id=entity_id,
        entry_type="payment",
        credit_paise=credit_paise,
        debit_paise=debit_paise,
        amount_paise=credit_paise or debit_paise,
        fee_paise=fee_paise,
        tax_paise=tax_paise,
        created_at=datetime(2026, 8, 29, 12, 0),
    )


def test_recomputes_net_from_credits_debits_fees_tax_and_adjustment_entries() -> None:
    entries = [
        settlement_entry("payment", credit_paise=100_000, fee_paise=2_000, tax_paise=360),
        settlement_entry("refund", debit_paise=25_000),
        settlement_entry("adjustment-credit", credit_paise=5_000),
    ]

    assert recompute_settlement_net(entries) == 77_640


def test_empty_settlement_has_zero_net() -> None:
    assert recompute_settlement_net([]) == 0
