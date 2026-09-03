"""Deterministic-first reconciliation orchestration using canonical input artifacts only."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import StrEnum
from hashlib import sha256
from json import dumps
from typing import Any, Self

from reconra.audit.events import AuditEvent
from reconra.matching.candidates import build_bank_candidates
from reconra.matching.exact import find_exact_payment_match
from reconra.matching.settlement_bank import find_exact_bank_match
from reconra.models.bank import BankTransaction
from reconra.models.exception import BreakClass, ReconciliationException, ResolutionStatus
from reconra.models.order import Order
from reconra.models.payment import Payment
from reconra.models.result import DeterministicMatch, ReconciliationResult
from reconra.models.settlement import SettlementEntry
from reconra.policy.reconciliation import ReconciliationPolicy
from reconra.reconciliation.settlement_math import recompute_settlement_net
from reconra.reconciliation.state import ReconciliationState


class ReconciliationStage(StrEnum):
    VALIDATED = "VALIDATED"
    NORMALIZED = "NORMALIZED"
    GROUPED_SETTLEMENTS = "GROUPED_SETTLEMENTS"
    EXACT_MATCHING_COMPLETE = "EXACT_MATCHING_COMPLETE"
    DETERMINISTIC_COMPLETE = "DETERMINISTIC_COMPLETE"


@dataclass(frozen=True, slots=True)
class CanonicalDataset:
    """The production reconciliation boundary, deliberately excluding generator truth."""

    orders: tuple[Order, ...]
    payments: tuple[Payment, ...]
    settlement_entries: tuple[SettlementEntry, ...]
    bank_transactions: tuple[BankTransaction, ...]

    @classmethod
    def from_raw_inputs(cls, raw_inputs: Mapping[str, object]) -> Self:
        """Normalize supported import artifacts into canonical models without generator imports."""
        orders = tuple(_order_from_raw(raw) for raw in _raw_records(raw_inputs, "orders"))
        payments = tuple(_payment_from_raw(raw) for raw in _raw_records(raw_inputs, "payments"))
        settlement_entries = tuple(
            _settlement_entry_from_raw(raw)
            for raw in _raw_records(raw_inputs, "reconciliation_rows")
        )
        bank_transactions = tuple(
            _bank_transaction_from_raw(raw)
            for raw in _raw_records(raw_inputs, "bank_transactions")
        )
        return cls(
            orders=orders,
            payments=payments,
            settlement_entries=settlement_entries,
            bank_transactions=bank_transactions,
        )

    def validate(self) -> tuple[str, ...]:
        """Reject malformed or unsafe canonical records before matching begins."""
        duplicate_order_ids = _validate_orders(self.orders)
        _require_unique_ids(self.payments, "payment_id")
        _require_unique_ids(self.settlement_entries, "entity_id")
        _require_unique_ids(self.bank_transactions, "bank_transaction_id")
        for transaction in self.bank_transactions:
            _require_non_negative_paise("bank credit_paise", transaction.credit_paise)
            _require_non_negative_paise("bank debit_paise", transaction.debit_paise)
        for entry in self.settlement_entries:
            for field_name in ("credit_paise", "debit_paise", "fee_paise", "tax_paise"):
                _require_non_negative_paise(field_name, getattr(entry, field_name))
        return duplicate_order_ids


def reconcile_deterministic(
    dataset: CanonicalDataset,
    policy: ReconciliationPolicy,
) -> ReconciliationResult:
    """Run deterministic matching and surface every unmatched bank credit as a residual."""
    if not isinstance(dataset, CanonicalDataset):
        raise TypeError("dataset must be a CanonicalDataset")
    if not isinstance(policy, ReconciliationPolicy):
        raise TypeError("policy must be a ReconciliationPolicy")

    duplicate_order_ids = dataset.validate()
    stages = [ReconciliationStage.VALIDATED.value, ReconciliationStage.NORMALIZED.value]
    run_id = _stable_run_id(dataset)
    event_timestamp = _audit_timestamp(dataset)
    total_bank_credit_paise = sum(row.credit_paise for row in dataset.bank_transactions)
    state = ReconciliationState(total_bank_credit_paise)
    audit_events: list[AuditEvent] = []
    duplicate_order_exceptions, duplicate_order_audits = _create_duplicate_order_residuals(
        duplicate_order_ids,
        run_id,
        event_timestamp,
    )
    audit_events.extend(duplicate_order_audits)

    payment_matches, payment_audits, matched_payment_ids, matched_entry_ids = _match_payments(
        dataset, run_id, event_timestamp
    )
    audit_events.extend(payment_audits)

    settlement_groups = _group_settlement_entries(dataset.settlement_entries)
    stages.append(ReconciliationStage.GROUPED_SETTLEMENTS.value)
    (
        settlement_bank_matches,
        settlement_audits,
        used_bank_ids,
        matched_settlement_ids,
    ) = _match_settlements_to_bank(
        settlement_groups,
        dataset.bank_transactions,
        policy,
        state,
        run_id,
        event_timestamp,
    )
    audit_events.extend(settlement_audits)
    stages.append(ReconciliationStage.EXACT_MATCHING_COMPLETE.value)

    bank_residuals, bank_residual_audits = _create_bank_residuals(
        settlement_groups,
        dataset.bank_transactions,
        used_bank_ids,
        policy,
        state,
        run_id,
        event_timestamp,
    )
    source_residuals, source_residual_audits = _create_source_residuals(
        dataset,
        settlement_groups,
        matched_payment_ids,
        matched_entry_ids,
        matched_settlement_ids,
        run_id,
        event_timestamp,
    )
    residual_exceptions = [*duplicate_order_exceptions, *bank_residuals, *source_residuals]
    audit_events.extend(bank_residual_audits)
    audit_events.extend(source_residual_audits)
    stages.append(ReconciliationStage.DETERMINISTIC_COMPLETE.value)

    return ReconciliationResult(
        run_id=run_id,
        total_bank_credit_paise=state.total_bank_credit_paise,
        explained_bank_credit_paise=state.explained_bank_credit_paise,
        unexplained_residual_paise=state.unexplained_residual_paise,
        exceptions=residual_exceptions,
        payment_matches=payment_matches,
        settlement_bank_matches=settlement_bank_matches,
        stages=stages,
        audit_events=audit_events,
        completed=True,
    )


def _match_payments(
    dataset: CanonicalDataset, run_id: str, timestamp: datetime
) -> tuple[list[DeterministicMatch], list[AuditEvent], set[str], set[str]]:
    matches: list[DeterministicMatch] = []
    audit_events: list[AuditEvent] = []
    matched_payment_ids: set[str] = set()
    matched_entry_ids: set[str] = set()
    entries = tuple(sorted(dataset.settlement_entries, key=lambda entry: entry.entity_id))
    for payment in sorted(dataset.payments, key=lambda item: item.payment_id):
        candidate = find_exact_payment_match(payment, entries)
        if candidate is None or candidate.candidate_id in matched_entry_ids:
            continue
        matched_payment_ids.add(payment.payment_id)
        matched_entry_ids.add(candidate.candidate_id)
        match = DeterministicMatch(
            source_id=candidate.source_id,
            candidate_id=candidate.candidate_id,
            evidence=list(candidate.evidence),
        )
        matches.append(match)
        audit_events.append(
            _audit_event(
                run_id=run_id,
                timestamp=timestamp,
                event_key=f"payment:{candidate.source_id}:{candidate.candidate_id}",
                action="EXACT_PAYMENT_MATCH",
                decision="MATCHED",
                financial_impact_paise=0,
                evidence=list(candidate.evidence),
            )
        )
    return matches, audit_events, matched_payment_ids, matched_entry_ids


def _group_settlement_entries(
    entries: Sequence[SettlementEntry],
) -> dict[str, tuple[SettlementEntry, ...]]:
    grouped: dict[str, list[SettlementEntry]] = defaultdict(list)
    for entry in sorted(entries, key=lambda item: item.entity_id):
        if entry.settlement_id is not None and entry.settled is not False:
            grouped[entry.settlement_id].append(entry)
    return {
        settlement_id: tuple(sorted(group_entries, key=lambda entry: entry.entity_id))
        for settlement_id, group_entries in sorted(grouped.items())
    }


def _match_settlements_to_bank(
    settlement_groups: Mapping[str, Sequence[SettlementEntry]],
    bank_transactions: Sequence[BankTransaction],
    policy: ReconciliationPolicy,
    state: ReconciliationState,
    run_id: str,
    timestamp: datetime,
) -> tuple[list[DeterministicMatch], list[AuditEvent], set[str], set[str]]:
    matches: list[DeterministicMatch] = []
    audit_events: list[AuditEvent] = []
    used_bank_ids: set[str] = set()
    matched_settlement_ids: set[str] = set()
    sorted_bank_rows = tuple(sorted(bank_transactions, key=lambda row: row.bank_transaction_id))
    for settlement_id, entries in settlement_groups.items():
        if not _consistent_settlement_utr(entries):
            continue
        expected_net_paise = recompute_settlement_net(entries)
        representative = entries[0]
        candidate = find_exact_bank_match(
            settlement_id=settlement_id,
            settlement_utr=representative.settlement_utr,
            expected_net_paise=expected_net_paise,
            settlement_date=(representative.settled_at or representative.created_at).date(),
            bank_transactions=tuple(
                row for row in sorted_bank_rows if row.bank_transaction_id not in used_bank_ids
            ),
            date_window_days=policy.settlement_date_window_days,
        )
        if candidate is None:
            continue
        bank_row = next(
            row for row in sorted_bank_rows if row.bank_transaction_id == candidate.candidate_id
        )
        used_bank_ids.add(bank_row.bank_transaction_id)
        matched_settlement_ids.add(settlement_id)
        before_state = _state_snapshot(state)
        state.commit_explanation(f"bank:{bank_row.bank_transaction_id}", bank_row.credit_paise)
        after_state = _state_snapshot(state)
        match = DeterministicMatch(
            source_id=candidate.source_id,
            candidate_id=candidate.candidate_id,
            evidence=list(candidate.evidence),
            financial_impact_paise=bank_row.credit_paise,
        )
        matches.append(match)
        audit_events.append(
            _audit_event(
                run_id=run_id,
                timestamp=timestamp,
                event_key=f"settlement:{candidate.source_id}:{candidate.candidate_id}",
                action="EXACT_SETTLEMENT_BANK_MATCH",
                decision="MATCHED",
                financial_impact_paise=bank_row.credit_paise,
                evidence=list(candidate.evidence),
                before_state=before_state,
                after_state=after_state,
            )
        )
    return matches, audit_events, used_bank_ids, matched_settlement_ids


def _create_bank_residuals(
    settlement_groups: Mapping[str, Sequence[SettlementEntry]],
    bank_transactions: Sequence[BankTransaction],
    used_bank_ids: set[str],
    policy: ReconciliationPolicy,
    state: ReconciliationState,
    run_id: str,
    timestamp: datetime,
) -> tuple[list[ReconciliationException], list[AuditEvent]]:
    residual_exceptions: list[ReconciliationException] = []
    audit_events: list[AuditEvent] = []
    fuzzy_candidate_ids = _fuzzy_candidate_ids(settlement_groups, bank_transactions, policy)
    for bank_row in sorted(bank_transactions, key=lambda row: row.bank_transaction_id):
        if bank_row.bank_transaction_id in used_bank_ids or bank_row.credit_paise == 0:
            continue
        exception_id = f"residual-bank-{bank_row.bank_transaction_id}"
        evidence = [f"bank_transaction_id:{bank_row.bank_transaction_id}"]
        evidence.append(
            "fuzzy_candidate_discovered"
            if bank_row.bank_transaction_id in fuzzy_candidate_ids
            else "no_supported_candidate"
        )
        residual_exceptions.append(
            ReconciliationException(
                exception_id=exception_id,
                break_class=BreakClass.UNRESOLVABLE,
                resolution_status=ResolutionStatus.ESCALATED,
                financial_impact_paise=bank_row.credit_paise,
                evidence=evidence,
            )
        )
        audit_events.append(
            _audit_event(
                run_id=run_id,
                timestamp=timestamp,
                event_key=exception_id,
                action="UNRESOLVED_BANK_RESIDUAL",
                decision="ESCALATED",
                financial_impact_paise=bank_row.credit_paise,
                evidence=evidence,
                exception_id=exception_id,
                verification_status="NOT_APPLIED",
                before_state=_state_snapshot(state),
                after_state=_state_snapshot(state),
            )
        )
    _assert_state_matches_residuals(state, residual_exceptions)
    return residual_exceptions, audit_events


def _create_source_residuals(
    dataset: CanonicalDataset,
    settlement_groups: Mapping[str, Sequence[SettlementEntry]],
    matched_payment_ids: set[str],
    matched_entry_ids: set[str],
    matched_settlement_ids: set[str],
    run_id: str,
    timestamp: datetime,
) -> tuple[list[ReconciliationException], list[AuditEvent]]:
    """Record unresolved source evidence without adding any amount to bank-credit tie-out."""
    exceptions: list[ReconciliationException] = []
    audit_events: list[AuditEvent] = []
    for payment in sorted(dataset.payments, key=lambda item: item.payment_id):
        if payment.payment_id in matched_payment_ids:
            continue
        exception_id = f"residual-payment-{payment.payment_id}"
        evidence = [f"payment_id:{payment.payment_id}", "no_unique_settlement_entry"]
        exceptions.append(
            ReconciliationException(
                exception_id=exception_id,
                break_class=BreakClass.MISSING_SETTLEMENT,
                resolution_status=ResolutionStatus.ESCALATED,
                financial_impact_paise=0,
                evidence=evidence,
            )
        )
        audit_events.append(
            _source_residual_audit(
                run_id, timestamp, exception_id, "MISSING_SETTLEMENT", evidence
            )
        )
    for entry in sorted(dataset.settlement_entries, key=lambda item: item.entity_id):
        if entry.entity_id in matched_entry_ids:
            continue
        exception_id = f"residual-settlement-entry-{entry.entity_id}"
        evidence = [f"settlement_entry_id:{entry.entity_id}", "no_unique_payment"]
        exceptions.append(
            ReconciliationException(
                exception_id=exception_id,
                break_class=BreakClass.MISSING_PAYMENT,
                resolution_status=ResolutionStatus.ESCALATED,
                financial_impact_paise=0,
                evidence=evidence,
            )
        )
        audit_events.append(
            _source_residual_audit(run_id, timestamp, exception_id, "MISSING_PAYMENT", evidence)
        )
    for settlement_id, entries in settlement_groups.items():
        if settlement_id in matched_settlement_ids:
            continue
        exception_id = f"residual-settlement-{settlement_id}"
        evidence = [
            f"settlement_id:{settlement_id}",
            f"expected_net_paise:{recompute_settlement_net(entries)}",
            "no_exact_bank_evidence",
        ]
        exceptions.append(
            ReconciliationException(
                exception_id=exception_id,
                break_class=BreakClass.MISSING_BANK_CREDIT,
                resolution_status=ResolutionStatus.ESCALATED,
                financial_impact_paise=0,
                evidence=evidence,
            )
        )
        audit_events.append(
            _source_residual_audit(run_id, timestamp, exception_id, "MISSING_BANK_CREDIT", evidence)
        )
    return exceptions, audit_events


def _create_duplicate_order_residuals(
    duplicate_order_ids: Sequence[str],
    run_id: str,
    timestamp: datetime,
) -> tuple[list[ReconciliationException], list[AuditEvent]]:
    """Expose exact duplicate orders as review evidence without affecting bank-credit math."""
    exceptions: list[ReconciliationException] = []
    audit_events: list[AuditEvent] = []
    for order_id in duplicate_order_ids:
        exception_id = f"duplicate-order-{order_id}"
        evidence = [f"order_id:{order_id}", "identical_canonical_order_rows"]
        exceptions.append(
            ReconciliationException(
                exception_id=exception_id,
                break_class=BreakClass.DUPLICATE_LEDGER_ROW,
                resolution_status=ResolutionStatus.ESCALATED,
                financial_impact_paise=0,
                evidence=evidence,
            )
        )
        audit_events.append(
            _source_residual_audit(
                run_id,
                timestamp,
                exception_id,
                "DUPLICATE_LEDGER_ROW",
                evidence,
            )
        )
    return exceptions, audit_events


def _source_residual_audit(
    run_id: str,
    timestamp: datetime,
    exception_id: str,
    action: str,
    evidence: list[str],
) -> AuditEvent:
    return _audit_event(
        run_id=run_id,
        timestamp=timestamp,
        event_key=exception_id,
        action=action,
        decision="ESCALATED",
        financial_impact_paise=0,
        evidence=evidence,
        exception_id=exception_id,
        verification_status="NOT_APPLIED",
    )


def _fuzzy_candidate_ids(
    settlement_groups: Mapping[str, Sequence[SettlementEntry]],
    bank_transactions: Sequence[BankTransaction],
    policy: ReconciliationPolicy,
) -> set[str]:
    candidate_ids: set[str] = set()
    for entries in settlement_groups.values():
        if not _consistent_settlement_utr(entries):
            continue
        expected_net_paise = recompute_settlement_net(entries)
        representative = entries[0].model_copy(
            update={
                "credit_paise": max(expected_net_paise, 0),
                "debit_paise": max(-expected_net_paise, 0),
                "fee_paise": 0,
                "tax_paise": 0,
            }
        )
        candidate_ids.update(
            candidate.candidate_id
            for candidate in build_bank_candidates(representative, bank_transactions, policy)
        )
    return candidate_ids


def _consistent_settlement_utr(entries: Sequence[SettlementEntry]) -> bool:
    return bool(entries) and len({entry.settlement_utr for entry in entries}) == 1


def _audit_event(
    *,
    run_id: str,
    timestamp: datetime,
    event_key: str,
    action: str,
    decision: str,
    financial_impact_paise: int,
    evidence: list[str],
    exception_id: str | None = None,
    verification_status: str = "VERIFIED",
    before_state: dict[str, int] | None = None,
    after_state: dict[str, int] | None = None,
) -> AuditEvent:
    return AuditEvent(
        event_id=_stable_identifier("event", event_key),
        run_id=run_id,
        timestamp=timestamp,
        actor="rule_engine",
        action=action,
        decision=decision,
        verification_status=verification_status,
        financial_impact_paise=financial_impact_paise,
        exception_id=exception_id,
        evidence=evidence,
        before_state=before_state or {},
        after_state=after_state or {},
    )


def _state_snapshot(state: ReconciliationState) -> dict[str, int]:
    return {
        "total_bank_credit_paise": state.total_bank_credit_paise,
        "explained_bank_credit_paise": state.explained_bank_credit_paise,
        "unexplained_residual_paise": state.unexplained_residual_paise,
    }


def _assert_state_matches_residuals(state: ReconciliationState, exceptions: Sequence[Any]) -> None:
    residual_paise = sum(exception.financial_impact_paise for exception in exceptions)
    if residual_paise != state.unexplained_residual_paise:
        raise RuntimeError("residual exceptions do not tie out to reconciliation state")


def _stable_run_id(dataset: CanonicalDataset) -> str:
    payload = {
        "orders": [
            order.model_dump(mode="json")
            for order in sorted(dataset.orders, key=lambda item: item.order_id)
        ],
        "payments": [
            payment.model_dump(mode="json")
            for payment in sorted(dataset.payments, key=lambda item: item.payment_id)
        ],
        "settlement_entries": [
            entry.model_dump(mode="json")
            for entry in sorted(dataset.settlement_entries, key=lambda item: item.entity_id)
        ],
        "bank_transactions": [
            transaction.model_dump(mode="json")
            for transaction in sorted(
                dataset.bank_transactions, key=lambda item: item.bank_transaction_id
            )
        ],
    }
    return _stable_identifier("run", dumps(payload, sort_keys=True, separators=(",", ":")))


def _stable_identifier(prefix: str, value: str) -> str:
    return f"{prefix}_{sha256(value.encode('utf-8')).hexdigest()[:20]}"


def _audit_timestamp(dataset: CanonicalDataset) -> datetime:
    timestamps = [order.created_at for order in dataset.orders]
    timestamps.extend(entry.created_at for entry in dataset.settlement_entries)
    timestamps.extend(payment.captured_at for payment in dataset.payments if payment.captured_at)
    if not timestamps:
        return datetime(1970, 1, 1, tzinfo=UTC)
    latest_timestamp = max(timestamps)
    if latest_timestamp.tzinfo is None:
        return latest_timestamp.replace(tzinfo=UTC)
    return latest_timestamp.astimezone(UTC)


def _raw_records(raw_inputs: Mapping[str, object], source_name: str) -> Sequence[Mapping[str, Any]]:
    value = raw_inputs.get(source_name)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{source_name} must be a sequence of records")
    if not all(isinstance(record, Mapping) for record in value):
        raise ValueError(f"{source_name} must contain mapping records")
    return value


def _order_from_raw(raw: Mapping[str, Any]) -> Order:
    return Order(
        order_id=raw["order_id"],
        receipt=raw.get("receipt"),
        created_at=_datetime_from_raw(raw["created_at"], "order created_at"),
        amount_paise=raw["amount_paise"],
        currency=raw.get("currency", "INR"),
        status=raw["status"],
    )


def _payment_from_raw(raw: Mapping[str, Any]) -> Payment:
    card_metadata = {
        key.removeprefix("card_"): value
        for key, value in raw.items()
        if key in {"card_type", "card_network", "card_issuer"} and isinstance(value, str)
    }
    return Payment(
        payment_id=raw["payment_id"],
        order_id=raw.get("order_id"),
        amount_paise=raw["amount_paise"],
        currency=raw.get("currency", "INR"),
        method=raw.get("method"),
        captured_at=_optional_datetime_from_raw(raw.get("captured_at"), "payment captured_at"),
        status=raw["status"],
        card_metadata=card_metadata or None,
    )


def _settlement_entry_from_raw(raw: Mapping[str, Any]) -> SettlementEntry:
    return SettlementEntry(
        entity_id=raw["entity_id"],
        entry_type=raw.get("entry_type", raw.get("type")),
        debit_paise=raw.get("debit_paise", raw.get("debit")),
        credit_paise=raw.get("credit_paise", raw.get("credit")),
        amount_paise=raw.get("amount_paise", raw.get("amount")),
        fee_paise=raw.get("fee_paise", raw.get("fee")),
        tax_paise=raw.get("tax_paise", raw.get("tax")),
        created_at=_datetime_from_raw(raw["created_at"], "settlement created_at"),
        currency=raw.get("currency", "INR"),
        on_hold=raw.get("on_hold"),
        settled=raw.get("settled"),
        settled_at=_optional_datetime_from_raw(raw.get("settled_at"), "settlement settled_at"),
        description=raw.get("description"),
        notes=raw.get("notes"),
        settlement_id=raw.get("settlement_id"),
        settlement_utr=raw.get("settlement_utr"),
        payment_id=raw.get("payment_id"),
        order_id=raw.get("order_id"),
        order_receipt=raw.get("order_receipt"),
        method=raw.get("method"),
        card_network=raw.get("card_network"),
        card_issuer=raw.get("card_issuer"),
        card_type=raw.get("card_type"),
        dispute_id=raw.get("dispute_id"),
    )


def _bank_transaction_from_raw(raw: Mapping[str, Any]) -> BankTransaction:
    return BankTransaction(
        bank_transaction_id=raw["bank_transaction_id"],
        transaction_date=_date_from_raw(raw["transaction_date"], "bank transaction_date"),
        value_date=_optional_date_from_raw(raw.get("value_date"), "bank value_date"),
        description=raw["description"],
        reference=raw.get("reference"),
        utr=raw.get("utr"),
        credit_paise=raw["credit_paise"],
        debit_paise=raw["debit_paise"],
    )


def _datetime_from_raw(value: object, field_name: str) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise TypeError(f"{field_name} must be a datetime or ISO datetime string")


def _optional_datetime_from_raw(value: object, field_name: str) -> datetime | None:
    if value is None:
        return None
    return _datetime_from_raw(value, field_name)


def _date_from_raw(value: object, field_name: str) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value)
    raise TypeError(f"{field_name} must be a date or ISO date string")


def _optional_date_from_raw(value: object, field_name: str) -> date | None:
    if value is None:
        return None
    return _date_from_raw(value, field_name)


def _require_unique_ids(records: Sequence[Any], field_name: str) -> None:
    identifiers = [getattr(record, field_name) for record in records]
    if any(not isinstance(identifier, str) or not identifier.strip() for identifier in identifiers):
        raise ValueError(f"{field_name} values must be non-empty strings")
    if len(set(identifiers)) != len(identifiers):
        raise ValueError(f"{field_name} values must be unique")


def _validate_orders(orders: Sequence[Order]) -> tuple[str, ...]:
    orders_by_id: dict[str, list[Order]] = defaultdict(list)
    for order in orders:
        if not isinstance(order.order_id, str) or not order.order_id.strip():
            raise ValueError("order_id values must be non-empty strings")
        orders_by_id[order.order_id].append(order)

    duplicate_order_ids: list[str] = []
    for order_id, records in sorted(orders_by_id.items()):
        if len(records) == 1:
            continue
        if any(record != records[0] for record in records[1:]):
            raise ValueError(f"conflicting duplicate order_id: {order_id}")
        duplicate_order_ids.append(order_id)
    return tuple(duplicate_order_ids)


def _require_non_negative_paise(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise TypeError(f"{field_name} must be an integer paise value")
    if value < 0:
        raise ValueError(f"{field_name} must not be negative")
