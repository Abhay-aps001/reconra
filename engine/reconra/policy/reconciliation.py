from typing import Self

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator


class ReconciliationPolicy(BaseModel):
    model_config = ConfigDict(strict=True)

    rounding_tolerance_paise: StrictInt = Field(default=0, ge=0)
    settlement_date_window_days: StrictInt = Field(default=2, ge=0)
    utr_similarity_threshold: float = Field(default=0.9, ge=0.0, le=1.0)
    narration_similarity_threshold: float = Field(default=0.9, ge=0.0, le=1.0)
    auto_apply_confidence_threshold: float = Field(default=0.98, ge=0.0, le=1.0)
    review_confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    high_impact_review_threshold_paise: StrictInt = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_confidence_thresholds(self) -> Self:
        if self.review_confidence_threshold > self.auto_apply_confidence_threshold:
            raise ValueError("review confidence threshold cannot exceed auto-apply threshold")
        return self
