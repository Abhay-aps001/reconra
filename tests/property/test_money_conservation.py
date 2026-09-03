from hypothesis import given
from hypothesis import strategies as st
from reconra.reconciliation.state import ReconciliationState


@st.composite
def valid_bank_credit_compositions(draw: st.DrawFn) -> tuple[int, list[int]]:
    total_bank_credit_paise = draw(st.integers(min_value=0, max_value=10**12))
    unexplained_paise = total_bank_credit_paise
    explanations: list[int] = []

    for _ in range(draw(st.integers(min_value=0, max_value=8))):
        explained_paise = draw(st.integers(min_value=0, max_value=unexplained_paise))
        explanations.append(explained_paise)
        unexplained_paise -= explained_paise

    return total_bank_credit_paise, explanations


@given(valid_bank_credit_compositions())
def test_every_committed_explanation_preserves_exact_money_conservation(
    composition: tuple[int, list[int]],
) -> None:
    total_bank_credit_paise, explanations = composition
    state = ReconciliationState(total_bank_credit_paise)

    for index, explained_paise in enumerate(explanations):
        assert state.commit_explanation(f"resolution_{index}", explained_paise) is True
        assert state.total_bank_credit_paise == (
            state.explained_bank_credit_paise + state.unexplained_residual_paise
        )


def test_reapplying_an_explanation_is_idempotent() -> None:
    state = ReconciliationState(10_000)

    assert state.commit_explanation("resolution_1", 7_000) is True
    assert state.commit_explanation("resolution_1", 7_000) is False
    assert state.explained_bank_credit_paise == 7_000
    assert state.unexplained_residual_paise == 3_000


def test_explanation_larger_than_remaining_credit_is_rejected_without_state_change() -> None:
    state = ReconciliationState(10_000)

    assert state.commit_explanation("resolution_1", 7_000) is True
    try:
        state.commit_explanation("resolution_2", 3_001)
    except ValueError:
        pass
    else:
        raise AssertionError("an explanation larger than the residual must be rejected")
    assert state.explained_bank_credit_paise == 7_000
    assert state.unexplained_residual_paise == 3_000
