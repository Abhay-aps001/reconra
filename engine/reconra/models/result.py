from pydantic import Field

from .base import CanonicalModel, PaiseField
from .exception import ReconciliationException


class ReconciliationResult(CanonicalModel):
    run_id: str
    total_bank_credit_paise: PaiseField
    explained_bank_credit_paise: PaiseField
    unexplained_residual_paise: PaiseField
    exceptions: list[ReconciliationException] = Field(default_factory=list)
