from datetime import datetime

from pydantic import Field

from .base import CanonicalModel, PaiseField


class Adjustment(CanonicalModel):
    adjustment_id: str
    amount_paise: PaiseField
    reason: str
    created_at: datetime
    settlement_id: str | None = None
    payment_id: str | None = None
    dispute_id: str | None = None
    source_metadata: dict[str, str] = Field(default_factory=dict)
