"""Sanitized residual evidence adapter for internal API-side orchestration."""

from dataclasses import dataclass
from datetime import date

from reconra.evidence.builder import EvidencePacket, build_evidence_packet
from reconra.matching.candidates import build_bank_candidates
from reconra.models.result import ReconciliationResult
from reconra.policy.reconciliation import ReconciliationPolicy
from reconra.reconciliation.pipeline import CanonicalDataset
from reconra.reconciliation.state import MatchCandidate


@dataclass(frozen=True, slots=True)
class ResidualCandidateFacts:
    """Existing deterministic candidate output retained without rescoring."""

    match: MatchCandidate


def bank_residual_candidate_facts(
    dataset: CanonicalDataset, bank_id: str, policy: ReconciliationPolicy
) -> list[ResidualCandidateFacts]:
    """Reuse Task 8 discovery and select only facts for the unresolved bank row."""
    bank_rows = tuple(
        row for row in dataset.bank_transactions if row.bank_transaction_id == bank_id
    )
    if not bank_rows:
        return []
    return [
        ResidualCandidateFacts(candidate)
        for settlement in dataset.settlement_entries
        for candidate in build_bank_candidates(settlement, bank_rows, policy)
    ]


def build_residual_packets(
    dataset: CanonicalDataset, result: ReconciliationResult, policy: ReconciliationPolicy
) -> list[EvidencePacket]:
    """Convert unresolved bank-credit residuals to bounded deterministic evidence only."""
    banks = {row.bank_transaction_id: row for row in dataset.bank_transactions}
    packets: list[EvidencePacket] = []
    for exception in result.exceptions:
        bank_id = next(
            (
                item.removeprefix("bank_transaction_id:")
                for item in exception.evidence
                if item.startswith("bank_transaction_id:")
            ),
            None,
        )
        bank = banks.get(bank_id) if bank_id is not None else None
        reference = (bank.utr or bank.reference or "") if bank is not None else ""
        target_date = (
            bank.transaction_date
            if bank is not None
            else _residual_date(dataset)
        )
        target_amount_paise = (
            bank.credit_paise if bank is not None else exception.financial_impact_paise
        )
        facts = bank_residual_candidate_facts(dataset, bank_id, policy) if bank_id else []
        packets.append(
            build_evidence_packet(
                case_id=exception.exception_id,
                target_amount_paise=target_amount_paise,
                target_date=target_date,
                reference_fragments=(reference[-16:],) if reference else (),
                candidates=(
                    {
                        "source_id": fact.match.source_id,
                        "candidate_id": fact.match.candidate_id,
                        "amount_delta_paise": fact.match.amount_delta_paise,
                        "date_delta_days": fact.match.date_delta_days,
                        "utr_similarity": fact.match.utr_similarity,
                        "narration_similarity": fact.match.narration_similarity,
                        "exact_amount": fact.match.exact_amount,
                        "normalized_similarity": max(
                            fact.match.utr_similarity or 0.0, fact.match.narration_similarity or 0.0
                        ),
                        "evidence": fact.match.evidence,
                    }
                    for fact in facts
                ),
                related_refund_count=0,
                related_adjustment_count=0,
                unresolved_reason=";".join(exception.evidence),
            )
        )
    return packets


def _residual_date(dataset: CanonicalDataset) -> date:
    if dataset.settlement_entries:
        return min(entry.created_at.date() for entry in dataset.settlement_entries)
    if dataset.bank_transactions:
        return min(row.transaction_date for row in dataset.bank_transactions)
    return date(1970, 1, 1)
