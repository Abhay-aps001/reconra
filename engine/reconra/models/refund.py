from datetime import datetime

from pydantic import Field

from .base import CanonicalModel, PaiseField


class Refund(CanonicalModel):
    refund_id: str
    payment_id: str | None = None
    amount_paise: PaiseField
    created_at: datetime
    status: str
    source_metadata: dict[str, str] = Field(default_factory=dict)
