from datetime import datetime

from pydantic import Field

from .base import CanonicalModel, PaiseField


class Payment(CanonicalModel):
    payment_id: str
    order_id: str | None = None
    amount_paise: PaiseField
    currency: str = "INR"
    method: str | None = None
    captured_at: datetime | None = None
    status: str
    card_metadata: dict[str, str] | None = None
    source_metadata: dict[str, str] = Field(default_factory=dict)
