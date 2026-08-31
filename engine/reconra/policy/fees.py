from pydantic import BaseModel, ConfigDict, Field, StrictInt


class FeePolicy(BaseModel):
    """Merchant-defined schedule inputs; calculation is intentionally out of scope."""

    model_config = ConfigDict(strict=True)

    currency: str = "INR"
    fee_bps_by_method: dict[str, StrictInt] = Field(default_factory=dict)
    tax_bps: StrictInt = 0
    settlement_cycle_days_by_method: dict[str, StrictInt] = Field(default_factory=dict)
    instant_settlement_enabled: bool = False
