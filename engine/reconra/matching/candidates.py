"""Conservative, non-mutating bank candidate discovery."""

from collections.abc import Sequence

from reconra.models.bank import BankTransaction
from reconra.models.settlement import SettlementEntry
from reconra.normalization.dates import date_distance_days
from reconra.normalization.ids import normalize_utr
from reconra.policy.reconciliation import ReconciliationPolicy
from reconra.reconciliation.settlement_math import recompute_settlement_net
from reconra.reconciliation.state import MatchCandidate

from .fuzzy import score_narration_similarity, score_utr_similarity
from .tolerance import within_rounding_tolerance


def build_bank_candidates(
    settlement: SettlementEntry,
    bank_rows: Sequence[BankTransaction],
    policy: ReconciliationPolicy,
) -> list[MatchCandidate]:
    """Return supported bank candidates without applying any reconciliation state changes."""
    expected_net_paise = recompute_settlement_net((settlement,))
    settlement_date = (settlement.settled_at or settlement.created_at).date()
    settlement_utr = normalize_utr(settlement.settlement_utr)
    settlement_narration = settlement.description or settlement.notes or ""
    source_id = settlement.settlement_id or settlement.entity_id
    candidates: list[MatchCandidate] = []

    for bank_row in bank_rows:
        actual_net_paise = bank_row.credit_paise - bank_row.debit_paise
        amount_delta_paise = abs(expected_net_paise - actual_net_paise)
        if not within_rounding_tolerance(expected_net_paise, actual_net_paise, policy):
            continue

        date_delta_days = date_distance_days(bank_row.transaction_date, settlement_date)
        if date_delta_days > policy.settlement_date_window_days:
            continue

        bank_utr = normalize_utr(bank_row.utr)
        utr_similarity = (
            score_utr_similarity(settlement_utr, bank_utr)
            if settlement_utr is not None and bank_utr is not None
            else None
        )
        narration_similarity = score_narration_similarity(
            settlement_narration,
            bank_row.description,
        )
        has_fuzzy_utr_evidence = (
            utr_similarity is not None
            and utr_similarity > 0.0
            and utr_similarity >= policy.utr_similarity_threshold
        )
        has_fuzzy_narration_evidence = (
            narration_similarity > 0.0
            and narration_similarity >= policy.narration_similarity_threshold
        )
        if not (has_fuzzy_utr_evidence or has_fuzzy_narration_evidence):
            continue

        exact_amount = amount_delta_paise == 0
        evidence: list[str] = []
        if has_fuzzy_utr_evidence:
            evidence.append("fuzzy_utr")
        if has_fuzzy_narration_evidence:
            evidence.append("fuzzy_narration")
        evidence.append("exact_amount" if exact_amount else "rounding_tolerance")
        evidence.append("date_within_policy_window")
        candidates.append(
            MatchCandidate(
                source_id=source_id,
                candidate_id=bank_row.bank_transaction_id,
                evidence=tuple(evidence),
                utr_similarity=utr_similarity,
                narration_similarity=narration_similarity,
                amount_delta_paise=amount_delta_paise,
                date_delta_days=date_delta_days,
                exact_amount=exact_amount,
            )
        )

    return sorted(candidates, key=lambda candidate: candidate.candidate_id)
