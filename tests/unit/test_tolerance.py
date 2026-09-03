import pytest
from reconra.matching.tolerance import within_rounding_tolerance
from reconra.policy.reconciliation import ReconciliationPolicy


@pytest.mark.parametrize(
    ("actual_paise", "expected_within_tolerance"),
    [
        (10_002, True),
        (10_003, True),
        (10_004, False),
    ],
)
def test_rounding_tolerance_honors_inside_boundary_and_one_paise_beyond(
    actual_paise: int,
    expected_within_tolerance: bool,
) -> None:
    policy = ReconciliationPolicy(rounding_tolerance_paise=3)

    assert (
        within_rounding_tolerance(
            expected_paise=10_000,
            actual_paise=actual_paise,
            policy=policy,
        )
        is expected_within_tolerance
    )


def test_rounding_tolerance_rejects_non_integer_paise_values() -> None:
    with pytest.raises(TypeError, match="expected_paise must be an integer paise value"):
        within_rounding_tolerance(
            expected_paise=10_000.0,  # type: ignore[arg-type]
            actual_paise=10_000,
            policy=ReconciliationPolicy(rounding_tolerance_paise=3),
        )
