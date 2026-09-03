from datetime import date, datetime

import pytest
from reconra.matching.exact import find_exact_payment_match
from reconra.matching.settlement_bank import find_exact_bank_match
from reconra.models.bank import BankTransaction
from reconra.models.payment import Payment
from reconra.models.settlement import SettlementEntry


def payment_entry(
    entity_id: str,
    payment_id: str | None,
    amount_paise: int,
) -> SettlementEntry:
    return SettlementEntry(
        entity_id=entity_id,
        entry_type="payment",
        debit_paise=0,
        credit_paise=amount_paise,
        amount_paise=amount_paise,
        fee_paise=0,
        tax_paise=0,
        created_at=datetime(2026, 8, 29, 12, 0),
        payment_id=payment_id,
    )


def bank_credit(
    bank_transaction_id: str,
    *,
    transaction_date: date,
    utr: str | None,
    credit_paise: int,
    debit_paise: int = 0,
) -> BankTransaction:
    return BankTransaction(
        bank_transaction_id=bank_transaction_id,
        transaction_date=transaction_date,
        description="Razorpay settlement",
        utr=utr,
        credit_paise=credit_paise,
        debit_paise=debit_paise,
    )


def test_exact_payment_id_and_amount_produce_evidenced_candidate() -> None:
    payment = Payment(payment_id="pay_123", amount_paise=49_900, status="captured")

    candidate = find_exact_payment_match(
        payment,
        [payment_entry("entry_123", " PAY_123 ", 49_900)],
    )

    assert candidate is not None
    assert candidate.source_id == "pay_123"
    assert candidate.candidate_id == "entry_123"
    assert candidate.evidence == ("payment_id", "amount_paise")


def test_same_payment_id_with_mismatched_amount_abstains() -> None:
    payment = Payment(payment_id="pay_123", amount_paise=49_900, status="captured")

    candidate = find_exact_payment_match(
        payment,
        [payment_entry("entry_wrong_amount", "pay_123", 49_899)],
    )

    assert candidate is None


def test_multiple_compatible_payment_entries_abstain_instead_of_forcing_a_match() -> None:
    payment = Payment(payment_id="pay_123", amount_paise=49_900, status="captured")

    candidate = find_exact_payment_match(
        payment,
        [
            payment_entry("entry_a", "pay_123", 49_900),
            payment_entry("entry_b", "pay_123", 49_900),
        ],
    )

    assert candidate is None


def test_exact_utr_amount_and_date_produce_bank_candidate() -> None:
    settlement_day = date(2026, 8, 30)

    candidate = find_exact_bank_match(
        settlement_id="setl_123",
        settlement_utr="UTR-123 456",
        expected_net_paise=77_640,
        settlement_date=settlement_day,
        bank_transactions=[
            bank_credit(
                "bank_123",
                transaction_date=settlement_day,
                utr="utr123456",
                credit_paise=77_640,
            )
        ],
        date_window_days=0,
    )

    assert candidate is not None
    assert candidate.source_id == "setl_123"
    assert candidate.candidate_id == "bank_123"
    assert candidate.evidence == ("settlement_utr", "credit_paise", "transaction_date")


def test_exact_utr_without_amount_compatibility_abstains() -> None:
    settlement_day = date(2026, 8, 30)

    candidate = find_exact_bank_match(
        settlement_id="setl_123",
        settlement_utr="UTR123456",
        expected_net_paise=77_640,
        settlement_date=settlement_day,
        bank_transactions=[
            bank_credit(
                "bank_wrong_amount",
                transaction_date=settlement_day,
                utr="UTR123456",
                credit_paise=77_639,
            )
        ],
        date_window_days=0,
    )

    assert candidate is None


def test_exact_utr_without_date_compatibility_abstains() -> None:
    candidate = find_exact_bank_match(
        settlement_id="setl_123",
        settlement_utr="UTR123456",
        expected_net_paise=77_640,
        settlement_date=date(2026, 8, 30),
        bank_transactions=[
            bank_credit(
                "bank_wrong_date",
                transaction_date=date(2026, 9, 2),
                utr="UTR123456",
                credit_paise=77_640,
            )
        ],
        date_window_days=1,
    )

    assert candidate is None


def test_exact_utr_matches_a_negative_settlement_net_to_a_bank_debit() -> None:
    settlement_day = date(2026, 8, 30)

    candidate = find_exact_bank_match(
        settlement_id="setl_debit",
        settlement_utr="UTR-DEBIT",
        expected_net_paise=-7_640,
        settlement_date=settlement_day,
        bank_transactions=[
            bank_credit(
                "bank_debit",
                transaction_date=settlement_day,
                utr="UTRDEBIT",
                credit_paise=0,
                debit_paise=7_640,
            )
        ],
        date_window_days=0,
    )

    assert candidate is not None
    assert candidate.candidate_id == "bank_debit"


@pytest.mark.parametrize("invalid_expected_net", [True, 7_640.0])
def test_exact_bank_match_rejects_non_integer_expected_net_paise(
    invalid_expected_net: object,
) -> None:
    with pytest.raises(TypeError, match="expected_net_paise must be an integer paise value"):
        find_exact_bank_match(
            settlement_id="setl_123",
            settlement_utr="UTR123456",
            expected_net_paise=invalid_expected_net,  # type: ignore[arg-type]
            settlement_date=date(2026, 8, 30),
            bank_transactions=[],
            date_window_days=0,
        )
