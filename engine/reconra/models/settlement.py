from datetime import datetime

from pydantic import Field

from .base import CanonicalModel, PaiseField


class SettlementEntry(CanonicalModel):
    entity_id: str
    entry_type: str
    debit_paise: PaiseField
    credit_paise: PaiseField
    amount_paise: PaiseField
    fee_paise: PaiseField
    tax_paise: PaiseField
    created_at: datetime
    currency: str = "INR"
    on_hold: bool | None = None
    settled: bool | None = None
    settled_at: datetime | None = None
    description: str | None = None
    notes: str | None = None
    settlement_id: str | None = None
    settlement_utr: str | None = None
    payment_id: str | None = None
    order_id: str | None = None
    order_receipt: str | None = None
    method: str | None = None
    card_network: str | None = None
    card_issuer: str | None = None
    card_type: str | None = None
    dispute_id: str | None = None
    source_metadata: dict[str, str] = Field(default_factory=dict)
