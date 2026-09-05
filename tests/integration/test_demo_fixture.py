from collections.abc import Iterator
from json import loads
from pathlib import Path

from reconra.policy.reconciliation import ReconciliationPolicy
from reconra.reconciliation.pipeline import CanonicalDataset, reconcile_deterministic

_INPUT_FILES = (
    "orders.json",
    "payments.json",
    "reconciliation_rows.json",
    "bank_transactions.json",
)
_PROHIBITED_METADATA = (
    "scenario",
    "clean",
    "messy",
    "mangled",
    "mngl",
    "partial_refund",
    "partial-refund",
    "refund_scenario",
    "duplicate",
    "missing",
    "unresolvable",
    "rounding_variance",
    "amount_mismatch",
    "fee_variance",
    "tax_variance",
    "cutoff",
    "delayed_settlement",
    "instant_settlement_variance",
    "dispute_adjustment",
    "general_adjustment",
    "ground_truth",
    "truth_",
    "expected_",
    "break_class",
)


def test_tracked_demo_fixture_contains_only_canonical_production_inputs() -> None:
    """The demo boundary contains ordinary inputs, not generator metadata or answers."""
    input_directory = Path(__file__).resolve().parents[2] / "data" / "demo" / "input"
    assert sorted(path.name for path in input_directory.iterdir()) == sorted(_INPUT_FILES)
    inputs = {
        Path(path).stem: loads((input_directory / path).read_text(encoding="utf-8"))
        for path in _INPUT_FILES
    }

    assert 240 <= len(inputs["reconciliation_rows"]) <= 250
    for filename, payload in inputs.items():
        for value in _strings_and_keys(payload):
            assert not any(token in value.lower() for token in _PROHIBITED_METADATA), filename

    order_ids = {row["order_id"] for row in inputs["orders"]}
    payment_ids = {row["payment_id"] for row in inputs["payments"]}
    assert all(
        row.get("order_id") is None or row["order_id"] in order_ids
        for row in inputs["payments"]
    )
    assert all(
        row.get("order_id") is None or row["order_id"] in order_ids
        for row in inputs["reconciliation_rows"]
    )
    assert all(
        row.get("payment_id") is None or row["payment_id"] in payment_ids
        for row in inputs["reconciliation_rows"]
    )
    settlement_ids = {row["settlement_id"] for row in inputs["reconciliation_rows"]}
    for row in inputs["bank_transactions"]:
        description = row["description"]
        if description.startswith("Razorpay settlement "):
            assert description.removeprefix("Razorpay settlement ") in settlement_ids
    for row in inputs["orders"] + inputs["payments"]:
        assert type(row["amount_paise"]) is int
    for row in inputs["reconciliation_rows"]:
        for field in ("credit", "debit", "amount", "fee", "tax"):
            assert type(row[field]) is int
    for row in inputs["bank_transactions"]:
        assert type(row["credit_paise"]) is int
        assert type(row["debit_paise"]) is int


def test_curated_demo_preserves_deterministic_financial_outputs() -> None:
    """Identifier sanitization must not alter the curated reconciliation behavior."""
    input_directory = Path(__file__).resolve().parents[2] / "data" / "demo" / "input"
    result = reconcile_deterministic(
        CanonicalDataset.from_raw_inputs(
            {
                Path(path).stem: loads((input_directory / path).read_text(encoding="utf-8"))
                for path in _INPUT_FILES
            }
        ),
        ReconciliationPolicy(),
    )

    assert result.completed is True
    assert result.total_bank_credit_paise == 185_990_200
    assert result.explained_bank_credit_paise == 185_001_500
    assert result.unexplained_residual_paise == 988_700
    assert len(result.payment_matches) == 243
    assert len(result.settlement_bank_matches) == 32
    assert len(result.exceptions) == 6
    assert result.total_bank_credit_paise == (
        result.explained_bank_credit_paise + result.unexplained_residual_paise
    )


def _strings_and_keys(value: object) -> Iterator[str]:
    if isinstance(value, dict):
        for key, nested in value.items():
            yield str(key)
            yield from _strings_and_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _strings_and_keys(nested)
    elif isinstance(value, str):
        yield value
