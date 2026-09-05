from reconra.reconciliation.state import ReconciliationState
from reconra.verification import idempotency


def test_duplicate_resolution_application_preserves_single_application_state() -> None:
    """Fails if retrying the same resolution changes the financial state a second time."""
    state = ReconciliationState(500)

    assert idempotency.apply_resolution_once(state, "run-1", "case-1", "AUTO_RESOLVE", 100) is True
    assert idempotency.apply_resolution_once(state, "run-1", "case-1", "AUTO_RESOLVE", 100) is False
    assert state.explained_bank_credit_paise == 100
    assert state.unexplained_residual_paise == 400
