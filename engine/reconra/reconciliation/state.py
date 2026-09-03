"""Minimal deterministic reconciliation state for exact tie-out accounting."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MatchCandidate:
    """A deterministic candidate and the explicit evidence supporting it."""

    source_id: str
    candidate_id: str
    evidence: tuple[str, ...]
    utr_similarity: float | None = None
    narration_similarity: float | None = None
    amount_delta_paise: int | None = None
    date_delta_days: int | None = None
    exact_amount: bool | None = None


class ReconciliationState:
    """Tracks the bank-credit tie-out for one reconciliation run."""

    def __init__(self, total_bank_credit_paise: int) -> None:
        self._require_non_negative_paise("total_bank_credit_paise", total_bank_credit_paise)
        self.total_bank_credit_paise = total_bank_credit_paise
        self.explained_bank_credit_paise = 0
        self.unexplained_residual_paise = total_bank_credit_paise
        self._committed_explanations: dict[str, int] = {}

    def commit_explanation(self, resolution_id: str, explained_paise: int) -> bool:
        """Commit one idempotent explained amount while preserving the tie-out."""
        if not isinstance(resolution_id, str) or not resolution_id.strip():
            raise ValueError("resolution_id must be a non-empty string")
        self._require_non_negative_paise("explained_paise", explained_paise)

        previous_amount = self._committed_explanations.get(resolution_id)
        if previous_amount is not None:
            if previous_amount != explained_paise:
                raise ValueError("resolution_id was already committed with a different amount")
            return False
        if explained_paise > self.unexplained_residual_paise:
            raise ValueError("explained_paise cannot exceed unexplained_residual_paise")

        self._committed_explanations[resolution_id] = explained_paise
        self.explained_bank_credit_paise += explained_paise
        self.unexplained_residual_paise -= explained_paise
        self._assert_money_conservation()
        return True

    @staticmethod
    def _require_non_negative_paise(field_name: str, value: int) -> None:
        if type(value) is not int:
            raise TypeError(f"{field_name} must be an integer paise value")
        if value < 0:
            raise ValueError(f"{field_name} must not be negative")

    def _assert_money_conservation(self) -> None:
        if self.total_bank_credit_paise != (
            self.explained_bank_credit_paise + self.unexplained_residual_paise
        ):
            raise RuntimeError("money conservation invariant violated")
