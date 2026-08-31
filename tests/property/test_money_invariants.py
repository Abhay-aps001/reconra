from datetime import datetime

from hypothesis import given
from hypothesis import strategies as st
from reconra.models.adjustment import Adjustment
from reconra.models.bank import BankTransaction
from reconra.models.exception import BreakClass, ReconciliationException, ResolutionStatus
from reconra.models.order import Order
from reconra.models.payment import Payment
from reconra.models.refund import Refund
from reconra.models.result import ReconciliationResult
from reconra.models.settlement import SettlementEntry


@given(st.integers(min_value=-(10**15), max_value=10**15))
def test_canonical_money_serialization_preserves_exact_integer_paise(amount_paise: int) -> None:
    now = datetime(2026, 8, 29, 12, 0)
    records = [
        Order(order_id="order", created_at=now, amount_paise=amount_paise, status="created"),
        Payment(payment_id="payment", amount_paise=amount_paise, status="captured"),
        Refund(
            refund_id="refund",
            payment_id="payment",
            amount_paise=amount_paise,
            created_at=now,
            status="processed",
        ),
        SettlementEntry(
            entity_id="entry",
            entry_type="payment",
            debit_paise=amount_paise,
            credit_paise=amount_paise,
            amount_paise=amount_paise,
            fee_paise=amount_paise,
            tax_paise=amount_paise,
            created_at=now,
        ),
        BankTransaction(
            bank_transaction_id="bank",
            transaction_date=now.date(),
            description="credit",
            credit_paise=amount_paise,
            debit_paise=amount_paise,
        ),
        Adjustment(
            adjustment_id="adjustment", amount_paise=amount_paise, reason="other", created_at=now
        ),
        ReconciliationException(
            exception_id="exception",
            break_class=BreakClass.UNRESOLVABLE,
            resolution_status=ResolutionStatus.ESCALATED,
            financial_impact_paise=amount_paise,
        ),
        ReconciliationResult(
            run_id="run",
            total_bank_credit_paise=amount_paise,
            explained_bank_credit_paise=amount_paise,
            unexplained_residual_paise=amount_paise,
        ),
    ]
    for record in records:
        restored = type(record).model_validate_json(record.model_dump_json())
        for field_name, value in restored.model_dump().items():
            if field_name.endswith("_paise"):
                assert value == amount_paise
                assert type(value) is int
