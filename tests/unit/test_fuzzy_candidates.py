from datetime import date, datetime

import pytest
from reconra.matching.candidates import build_bank_candidates
from reconra.matching.fuzzy import score_narration_similarity, score_utr_similarity
from reconra.models.bank import BankTransaction
from reconra.models.settlement import SettlementEntry
from reconra.policy.reconciliation import ReconciliationPolicy


def settlement(
    *,
    settlement_utr: str = "UTR-2026-ABC-12345",
    description: str = "Razorpay settlement Acme Stores",
) -> SettlementEntry:
    return SettlementEntry(
        entity_id="entry_123",
        settlement_id="setl_123",
        settlement_utr=settlement_utr,
        entry_type="payment",
        credit_paise=100_000,
        debit_paise=0,
        amount_paise=100_000,
        fee_paise=0,
        tax_paise=0,
        created_at=datetime(2026, 8, 30, 12, 0),
        settled_at=datetime(2026, 8, 30, 12, 0),
        description=description,
    )


def bank_row(
    bank_transaction_id: str,
    *,
    credit_paise: int = 100_000,
    utr: str = "UTR 2026 ABC 1234",
    description: str = "Acme Stores Razorpay settlement",
) -> BankTransaction:
    return BankTransaction(
        bank_transaction_id=bank_transaction_id,
        transaction_date=date(2026, 8, 31),
        description=description,
        utr=utr,
        credit_paise=credit_paise,
        debit_paise=0,
    )


def test_rapidfuzz_scores_clipped_utr_and_reordered_narration_as_similar() -> None:
    assert score_utr_similarity("UTR-2026-ABC-12345", "utr 2026 abc 1234") > 0.9
    assert score_narration_similarity(
        "Razorpay settlement Acme Stores",
        "Acme Stores Razorpay settlement",
    ) == pytest.approx(1.0)


def test_clipped_utr_with_exact_amount_and_in_window_date_creates_evidenced_candidate() -> None:
    candidates = build_bank_candidates(
        settlement(),
        [bank_row("bank_clipped_utr")],
        ReconciliationPolicy(
            settlement_date_window_days=1,
            utr_similarity_threshold=0.9,
            narration_similarity_threshold=0.9,
        ),
    )

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.source_id == "setl_123"
    assert candidate.candidate_id == "bank_clipped_utr"
    assert candidate.utr_similarity is not None
    assert candidate.utr_similarity > 0.9
    assert candidate.narration_similarity == pytest.approx(1.0)
    assert candidate.amount_delta_paise == 0
    assert candidate.date_delta_days == 1
    assert candidate.exact_amount is True
    assert candidate.evidence == (
        "fuzzy_utr",
        "fuzzy_narration",
        "exact_amount",
        "date_within_policy_window",
    )


def test_similar_text_with_large_amount_mismatch_does_not_create_candidate() -> None:
    candidates = build_bank_candidates(
        settlement(),
        [
            bank_row(
                "bank_wrong_amount",
                credit_paise=95_000,
                utr="UNRELATED-REFERENCE",
            )
        ],
        ReconciliationPolicy(rounding_tolerance_paise=3, settlement_date_window_days=1),
    )

    assert candidates == []


def test_zero_similarity_with_zero_threshold_does_not_create_candidate() -> None:
    candidates = build_bank_candidates(
        settlement(settlement_utr="", description=""),
        [bank_row("bank_empty_evidence", utr="", description="")],
        ReconciliationPolicy(
            settlement_date_window_days=1,
            utr_similarity_threshold=0.0,
            narration_similarity_threshold=0.0,
        ),
    )

    assert candidates == []


def test_bank_candidates_have_deterministic_id_order_without_applying_matches() -> None:
    candidates = build_bank_candidates(
        settlement(),
        [bank_row("bank_z"), bank_row("bank_a")],
        ReconciliationPolicy(settlement_date_window_days=1),
    )

    assert [candidate.candidate_id for candidate in candidates] == ["bank_a", "bank_z"]
