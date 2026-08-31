from datetime import datetime

import pytest
from pydantic import ValidationError
from reconra.models.adjustment import Adjustment
from reconra.models.bank import BankTransaction
from reconra.models.exception import BreakClass, ReconciliationException, ResolutionStatus
from reconra.models.order import Order
from reconra.models.payment import Payment
from reconra.models.refund import Refund
from reconra.models.result import ReconciliationResult
from reconra.models.settlement import SettlementEntry
from reconra.policy.reconciliation import ReconciliationPolicy


def test_canonical_payment_preserves_integer_paise_through_json() -> None:
    payment = Payment(payment_id="pay_1", amount_paise=274950, status="captured", order_id=None)
    restored = Payment.model_validate_json(payment.model_dump_json())
    assert restored.amount_paise == 274950
    assert type(restored.amount_paise) is int
    assert restored.order_id is None


def test_monetary_fields_reject_float() -> None:
    with pytest.raises(ValidationError):
        Payment(payment_id="pay_1", amount_paise=1.0, status="captured")


@pytest.mark.parametrize("invalid", [1.0, True, "1"])
def test_all_canonical_monetary_fields_are_strict_ints(invalid: object) -> None:
    with pytest.raises(ValidationError):
        Order(order_id="order_1", created_at=datetime.now(), amount_paise=invalid, status="created")
    with pytest.raises(ValidationError):
        Payment(payment_id="pay_1", amount_paise=invalid, status="captured")
    with pytest.raises(ValidationError):
        Refund(
            refund_id="rfnd_1", amount_paise=invalid, created_at=datetime.now(), status="processed"
        )
    with pytest.raises(ValidationError):
        SettlementEntry(
            entity_id="ent_1",
            entry_type="payment",
            debit_paise=invalid,
            credit_paise=0,
            amount_paise=0,
            fee_paise=0,
            tax_paise=0,
            created_at=datetime.now(),
        )
    with pytest.raises(ValidationError):
        BankTransaction(
            bank_transaction_id="bank_1",
            transaction_date=datetime.now().date(),
            description="credit",
            credit_paise=invalid,
            debit_paise=0,
        )
    with pytest.raises(ValidationError):
        Adjustment(
            adjustment_id="adj_1", amount_paise=invalid, reason="fee", created_at=datetime.now()
        )
    with pytest.raises(ValidationError):
        ReconciliationException(
            exception_id="exc_1",
            break_class=BreakClass.UNRESOLVABLE,
            resolution_status=ResolutionStatus.ESCALATED,
            financial_impact_paise=invalid,
        )
    with pytest.raises(ValidationError):
        ReconciliationResult(
            run_id="run_1",
            total_bank_credit_paise=invalid,
            explained_bank_credit_paise=0,
            unexplained_residual_paise=0,
        )


def test_settlement_entry_preserves_approved_source_evidence() -> None:
    entry = SettlementEntry(
        entity_id="ent_1",
        entry_type="payment",
        debit_paise=0,
        credit_paise=100,
        amount_paise=100,
        fee_paise=2,
        tax_paise=0,
        currency="INR",
        on_hold=False,
        settled=True,
        created_at=datetime(2026, 8, 29, 10, 0),
        settled_at=datetime(2026, 8, 30, 10, 0),
        description="Payment",
        notes="note",
        order_receipt="receipt_1",
        card_network="Visa",
        card_issuer="Bank",
        card_type="credit",
    )
    expected = {
        "currency": "INR",
        "on_hold": False,
        "settled": True,
        "settled_at": datetime(2026, 8, 30, 10, 0),
        "description": "Payment",
        "notes": "note",
        "order_receipt": "receipt_1",
        "card_network": "Visa",
        "card_issuer": "Bank",
        "card_type": "credit",
    }
    dumped = entry.model_dump()
    for field_name, value in expected.items():
        assert field_name in SettlementEntry.model_fields
        assert dumped[field_name] == value
    assert SettlementEntry.model_validate_json(entry.model_dump_json()) == entry


@pytest.mark.parametrize(
    "kwargs",
    [
        {"rounding_tolerance_paise": -1},
        {"settlement_date_window_days": -1},
        {"high_impact_review_threshold_paise": -1},
        {"review_confidence_threshold": 0.9, "auto_apply_confidence_threshold": 0.8},
    ],
)
def test_policy_rejects_unsafe_configuration(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        ReconciliationPolicy(**kwargs)


def test_order_validates_canonical_record() -> None:
    order = Order(
        order_id="order_1",
        created_at=datetime(2026, 8, 29, 12, 0),
        amount_paise=49900,
        status="created",
    )
    assert order.amount_paise == 49900


def test_enum_serialization_is_deterministic() -> None:
    assert BreakClass.AMOUNT_MISMATCH.value == "AMOUNT_MISMATCH"
    assert ResolutionStatus.REVIEW_REQUIRED.value == "REVIEW_REQUIRED"


def test_policy_validates_configuration_ranges() -> None:
    assert ReconciliationPolicy(utr_similarity_threshold=0.8).utr_similarity_threshold == 0.8
    with pytest.raises(ValidationError):
        ReconciliationPolicy(utr_similarity_threshold=1.1)
