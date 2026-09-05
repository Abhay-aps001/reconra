from reconra.reconciliation.state import ReconciliationState
from reconra.verification import idempotency


def test_applied_resolution_preserves_exact_paise_conservation() -> None:
    """Fails if applying a verified resolution breaks the bank-credit tie-out."""
    state = ReconciliationState(500)

    idempotency.apply_resolution_once(state, "run-1", "case-1", "AUTO_RESOLVE", 100)

    assert state.total_bank_credit_paise == (
        state.explained_bank_credit_paise + state.unexplained_residual_paise
    )
