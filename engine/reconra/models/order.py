from datetime import datetime

from pydantic import Field

from .base import CanonicalModel, PaiseField


class Order(CanonicalModel):
    order_id: str
    receipt: str | None = None
    created_at: datetime
    amount_paise: PaiseField
    currency: str = "INR"
    status: str
    source_metadata: dict[str, str] = Field(default_factory=dict)
