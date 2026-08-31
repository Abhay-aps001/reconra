from datetime import date

from pydantic import Field

from .base import CanonicalModel, PaiseField


class BankTransaction(CanonicalModel):
    bank_transaction_id: str
    transaction_date: date
    value_date: date | None = None
    description: str
    reference: str | None = None
    utr: str | None = None
    credit_paise: PaiseField
    debit_paise: PaiseField
    source_metadata: dict[str, str] = Field(default_factory=dict)
