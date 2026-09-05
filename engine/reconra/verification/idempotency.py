"""Stable, exact-paIse resolution-application helper."""

from reconra.reconciliation.state import ReconciliationState


def apply_resolution_once(
    state: ReconciliationState,
    run_id: str,
    exception_id: str,
    action: str,
    financial_impact_paise: int,
) -> bool:
    """Apply a current verified resolution once through the state tie-out guard."""
    resolution_id = f"{run_id}:{exception_id}:{action}"
    return state.commit_explanation(resolution_id, financial_impact_paise)
