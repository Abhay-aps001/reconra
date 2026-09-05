from datetime import date, datetime

from app.services.residual_adapter import bank_residual_candidate_facts, build_residual_packets
from reconra.matching.candidates import build_bank_candidates
from reconra.models.bank import BankTransaction
from reconra.models.exception import BreakClass, ReconciliationException, ResolutionStatus
from reconra.models.result import ReconciliationResult
from reconra.models.settlement import SettlementEntry
from reconra.policy.reconciliation import ReconciliationPolicy
from reconra.reconciliation.pipeline import CanonicalDataset
from reconra.reconciliation.state import ReconciliationState


def _dataset(bank: BankTransaction) -> CanonicalDataset:
    settlement = SettlementEntry(
        entity_id="entry-1",
        settlement_id="setl-1",
        settlement_utr="UTR-2026-ABC-12345",
        entry_type="payment",
        credit_paise=100_000,
        debit_paise=0,
        amount_paise=100_000,
        fee_paise=0,
        tax_paise=0,
        created_at=datetime(2026, 8, 30),
        settled_at=datetime(2026, 8, 30),
        description="Razorpay settlement Acme Stores",
    )
    return CanonicalDataset(
        orders=(), payments=(), settlement_entries=(settlement,), bank_transactions=(bank,)
    )


def _bank(identifier: str = "bank-1", credit_paise: int = 100_000) -> BankTransaction:
    return BankTransaction(
        bank_transaction_id=identifier,
        transaction_date=date(2026, 8, 31),
        description="Acme Stores Razorpay settlement",
        utr="UTR 2026 ABC 1234",
        credit_paise=credit_paise,
        debit_paise=0,
    )


def test_candidate_facts_preserve_real_task8_candidate_evidence_without_state_mutation() -> None:
    """Fails if adapter rescoring, invention, or extraction mutates reconciliation money state."""
    dataset = _dataset(_bank())
    policy = ReconciliationPolicy(settlement_date_window_days=1)
    state = ReconciliationState(100_000)
    before = (state.explained_bank_credit_paise, state.unexplained_residual_paise)
    facts = bank_residual_candidate_facts(dataset, "bank-1", policy)
    direct = build_bank_candidates(dataset.settlement_entries[0], dataset.bank_transactions, policy)

    assert (
        [fact.match.candidate_id for fact in facts]
        == [candidate.candidate_id for candidate in direct]
        == ["bank-1"]
    )
    assert type(facts[0].match.amount_delta_paise) is int
    assert facts[0].match.date_delta_days == direct[0].date_delta_days
    assert facts[0].match.evidence == direct[0].evidence
    assert facts[0].match.exact_amount is True
    assert before == (state.explained_bank_credit_paise, state.unexplained_residual_paise)


def test_residual_packet_retains_task8_candidate_binding_facts() -> None:
    dataset = _dataset(_bank())
    result = ReconciliationResult(
        run_id="run-1", total_bank_credit_paise=100_000, explained_bank_credit_paise=0,
        unexplained_residual_paise=100_000, exceptions=[ReconciliationException(
            exception_id="residual-bank-bank-1", break_class=BreakClass.UNRESOLVABLE,
            resolution_status=ResolutionStatus.ESCALATED, financial_impact_paise=100_000,
            evidence=["bank_transaction_id:bank-1"],
        )], completed=True,
    )

    candidate = build_residual_packets(dataset, result, ReconciliationPolicy())[0].candidates[0]

    assert candidate.source_id == "setl-1"
    assert candidate.candidate_id == "bank-1"
    assert candidate.amount_delta_paise == 0
    assert candidate.date_delta_days == 1
    assert candidate.utr_similarity is not None
    assert candidate.narration_similarity is not None
    assert candidate.exact_amount is True


def test_candidate_adapter_excludes_incompatible_rows_and_serializes_no_private_data() -> None:
    """Fails if adapter invents an ineligible candidate or retains prohibited content."""
    facts = bank_residual_candidate_facts(
        _dataset(_bank(credit_paise=90_000)), "bank-1", ReconciliationPolicy()
    )

    assert facts == []
    assert all(
        word not in str(facts).lower()
        for word in (
            "email",
            "phone",
            "account",
            "truth",
            "scenario",
            "generator",
            "secret",
            "raw_document",
        )
    )


def test_residual_without_bank_identifier_retains_sanitized_packet_without_candidates(
    monkeypatch,
) -> None:
    """Fails if a non-bank residual is dropped or invents bank candidate discovery."""
    from app.services import residual_adapter

    dataset = _dataset(_bank())
    result = ReconciliationResult(
        run_id="run-1", total_bank_credit_paise=0, explained_bank_credit_paise=0,
        unexplained_residual_paise=0,
        exceptions=[ReconciliationException(
            exception_id="residual-source-1",
            break_class=BreakClass.MISSING_PAYMENT,
            resolution_status=ResolutionStatus.ESCALATED,
            financial_impact_paise=0,
            evidence=["payment_id:missing", "no_unique_settlement_entry"],
        )],
        completed=True,
    )
    def unexpected_discovery(*args):
        raise AssertionError("unexpected discovery")

    monkeypatch.setattr(residual_adapter, "bank_residual_candidate_facts", unexpected_discovery)

    packets = residual_adapter.build_residual_packets(dataset, result, ReconciliationPolicy())

    assert len(packets) == 1
    assert packets[0].candidates == ()
    assert packets[0].unresolved_reason == "payment_id:missing;no_unique_settlement_entry"
