"""Policy-configured monetary tolerance checks."""

from reconra.policy.reconciliation import ReconciliationPolicy


def within_rounding_tolerance(
    expected_paise: int,
    actual_paise: int,
    policy: ReconciliationPolicy,
) -> bool:
    """Return whether two paise amounts are compatible under policy."""
    if type(expected_paise) is not int:
        raise TypeError("expected_paise must be an integer paise value")
    if type(actual_paise) is not int:
        raise TypeError("actual_paise must be an integer paise value")
    return abs(expected_paise - actual_paise) <= policy.rounding_tolerance_paise
