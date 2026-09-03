from __future__ import annotations

from copy import deepcopy
from typing import Any

from hypothesis import given
from hypothesis import strategies as st
from reconra.policy.reconciliation import ReconciliationPolicy
from reconra.reconciliation.pipeline import CanonicalDataset, reconcile_deterministic

from generator.src.clean import generate_clean_dataset


def _match_keys(result: Any) -> tuple[tuple[str, str], tuple[str, str]]:
    return (
        tuple((match.source_id, match.candidate_id) for match in result.payment_matches),
        tuple((match.source_id, match.candidate_id) for match in result.settlement_bank_matches),
    )


@given(st.data())
def test_shuffling_canonical_input_rows_cannot_change_deterministic_matches_or_tie_out(
    data: st.DataObject,
) -> None:
    """Fails if matching depends on input row order instead of deterministic evidence."""
    raw_inputs = generate_clean_dataset(seed=1101).raw_inputs
    baseline = reconcile_deterministic(
        CanonicalDataset.from_raw_inputs(raw_inputs),
        ReconciliationPolicy(),
    )
    shuffled = deepcopy(raw_inputs)
    for source_name in ("orders", "payments", "reconciliation_rows", "bank_transactions"):
        shuffled[source_name] = list(data.draw(st.permutations(shuffled[source_name])))

    result = reconcile_deterministic(
        CanonicalDataset.from_raw_inputs(shuffled),
        ReconciliationPolicy(),
    )

    assert result.run_id == baseline.run_id
    assert _match_keys(result) == _match_keys(baseline)
    assert result.total_bank_credit_paise == baseline.total_bank_credit_paise
    assert result.explained_bank_credit_paise == baseline.explained_bank_credit_paise
    assert result.unexplained_residual_paise == baseline.unexplained_residual_paise
