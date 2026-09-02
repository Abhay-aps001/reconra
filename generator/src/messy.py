from __future__ import annotations

from hashlib import sha256
from json import dumps
from typing import Any

from reconra.models.exception import BreakClass

from generator.scenarios.distribution import ScenarioDistribution

from .bank import bank_transaction_for_settlement, generate_bank_transactions
from .clean import GeneratedDataset
from .merchant import RawRecord, generate_orders_and_payments
from .razorpay_recon import generate_reconciliation_rows
from .truth import create_ground_truth, create_ground_truth_case


def _require_integer(record: RawRecord, field_name: str) -> int:
    value = record[field_name]
    if type(value) is not int:
        raise TypeError(f"{field_name} must be an integer")
    return value


def _require_string(record: RawRecord, field_name: str) -> str:
    value = record[field_name]
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    return value


def _settlement_rows(
    raw_inputs: dict[str, list[RawRecord]], settlement_utr: str
) -> list[RawRecord]:
    return [
        row
        for row in raw_inputs["reconciliation_rows"]
        if row["settlement_utr"] == settlement_utr
    ]


def _bank_transaction_id_for_settlement(
    raw_inputs: dict[str, list[RawRecord]], settlement_utr: str, default: str
) -> str:
    for bank_transaction in raw_inputs["bank_transactions"]:
        if bank_transaction["utr"] == settlement_utr:
            return _require_string(bank_transaction, "bank_transaction_id")
    return default


def _recompute_settlement_bank_evidence(
    raw_inputs: dict[str, list[RawRecord]],
    settlement_utr: str,
    bank_transaction_id: str,
) -> None:
    bank_transactions = raw_inputs["bank_transactions"]
    bank_transactions[:] = [
        transaction for transaction in bank_transactions if transaction["utr"] != settlement_utr
    ]
    reconciliation_rows = _settlement_rows(raw_inputs, settlement_utr)
    if reconciliation_rows:
        bank_transactions.append(
            bank_transaction_for_settlement(reconciliation_rows, bank_transaction_id)
        )


def _remove_settlement_bank_evidence(
    raw_inputs: dict[str, list[RawRecord]], settlement_utr: str
) -> None:
    raw_inputs["bank_transactions"][:] = [
        transaction
        for transaction in raw_inputs["bank_transactions"]
        if transaction["utr"] != settlement_utr
    ]


def _isolate_scenario_settlement(
    raw_inputs: dict[str, list[RawRecord]], row: RawRecord, case_number: int
) -> str:
    original_settlement_utr = _require_string(row, "settlement_utr")
    original_bank_transaction_id = _bank_transaction_id_for_settlement(
        raw_inputs,
        original_settlement_utr,
        default=f"bank_rebuilt_{case_number:03d}",
    )
    scenario_settlement_id = f"setl_scenario_{case_number:03d}"
    scenario_settlement_utr = f"UTR-SCENARIO-{case_number:03d}"

    row["settlement_id"] = scenario_settlement_id
    row["settlement_utr"] = scenario_settlement_utr
    _recompute_settlement_bank_evidence(
        raw_inputs, original_settlement_utr, original_bank_transaction_id
    )
    _recompute_settlement_bank_evidence(
        raw_inputs, scenario_settlement_utr, f"bank_scenario_{case_number:03d}"
    )
    return scenario_settlement_utr


def _adjustment_row(
    entity_id: str, payment_row: RawRecord, amount_paise: int, dispute_id: str | None
) -> RawRecord:
    return {
        "entity_id": entity_id,
        "type": "adjustment",
        "debit": amount_paise,
        "credit": 0,
        "amount": amount_paise,
        "currency": "INR",
        "fee": 0,
        "tax": 0,
        "on_hold": False,
        "settled": True,
        "created_at": payment_row["created_at"],
        "settled_at": payment_row["settled_at"],
        "settlement_id": payment_row["settlement_id"],
        "description": "Settlement adjustment",
        "notes": None,
        "payment_id": None,
        "settlement_utr": payment_row["settlement_utr"],
        "order_id": None,
        "order_receipt": None,
        "method": None,
        "card_network": None,
        "card_issuer": None,
        "card_type": None,
        "dispute_id": dispute_id,
    }


def _refund_row(entity_id: str, payment_row: RawRecord, amount_paise: int) -> RawRecord:
    return {
        "entity_id": entity_id,
        "type": "refund",
        "debit": amount_paise,
        "credit": 0,
        "amount": amount_paise,
        "currency": "INR",
        "fee": 0,
        "tax": 0,
        "on_hold": False,
        "settled": True,
        "created_at": payment_row["created_at"],
        "settled_at": payment_row["settled_at"],
        "settlement_id": payment_row["settlement_id"],
        "description": "Processed refund",
        "notes": None,
        "payment_id": payment_row["payment_id"],
        "settlement_utr": payment_row["settlement_utr"],
        "order_id": payment_row["order_id"],
        "order_receipt": payment_row["order_receipt"],
        "method": payment_row["method"],
        "card_network": payment_row["card_network"],
        "card_issuer": payment_row["card_issuer"],
        "card_type": payment_row["card_type"],
        "dispute_id": None,
    }


def _inject_scenario(
    break_class: BreakClass,
    case_number: int,
    raw_inputs: dict[str, list[RawRecord]],
    target_row: RawRecord,
    scenario_settlement_utr: str,
) -> str:
    reconciliation_rows = raw_inputs["reconciliation_rows"]
    target_entity_id = _require_string(target_row, "entity_id")

    if break_class is BreakClass.ROUNDING_VARIANCE:
        target_row["credit"] = _require_integer(target_row, "credit") - 1
    elif break_class is BreakClass.AMOUNT_MISMATCH:
        target_row["amount"] = _require_integer(target_row, "amount") + 100
    elif break_class is BreakClass.FEE_VARIANCE:
        target_row["fee"] = 137
    elif break_class is BreakClass.TAX_VARIANCE:
        target_row["tax"] = 25
    elif break_class is BreakClass.SETTLEMENT_CUTOFF:
        target_row["settled_at"] = "2026-01-19T23:59:00+00:00"
    elif break_class is BreakClass.DELAYED_SETTLEMENT:
        target_row["settled_at"] = "2026-02-20T12:00:00+00:00"
    elif break_class is BreakClass.INSTANT_SETTLEMENT_VARIANCE:
        target_row["settled_at"] = target_row["created_at"]
        target_row["fee"] = 199
    elif break_class is BreakClass.REFUND_NETTED_LATER:
        target_row["settled_at"] = "2026-02-10T12:00:00+00:00"
        refund = _refund_row(
            entity_id=f"refund_later_{case_number:03d}",
            payment_row=target_row,
            amount_paise=max(1, _require_integer(target_row, "amount") // 3),
        )
        reconciliation_rows.append(refund)
        return _require_string(refund, "entity_id")
    elif break_class is BreakClass.PARTIAL_REFUND:
        target_row["settled_at"] = "2026-02-03T12:00:00+00:00"
        refund = _refund_row(
            entity_id=f"partial_refund_{case_number:03d}",
            payment_row=target_row,
            amount_paise=max(1, _require_integer(target_row, "amount") // 2),
        )
        reconciliation_rows.append(refund)
        return _require_string(refund, "entity_id")
    elif break_class is BreakClass.MANGLED_UTR:
        target_row["settlement_utr"] = f"MNGLED-{case_number:03d}"
    elif break_class is BreakClass.MANGLED_NARRATION:
        for bank_transaction in raw_inputs["bank_transactions"]:
            if bank_transaction["utr"] == scenario_settlement_utr:
                bank_transaction["bank_transaction_id"] = f"bank_narration_{case_number:03d}"
                bank_transaction["description"] = "RZPY STLMNT ??"
                bank_transaction["utr"] = f"NARR-MNGL-{case_number:03d}"
                bank_transaction["reference"] = f"NARR-MNGL-{case_number:03d}"
                break
    elif break_class is BreakClass.DUPLICATE_LEDGER_ROW:
        duplicate_order = dict(
            raw_inputs["orders"][case_number % len(raw_inputs["orders"])]
        )
        raw_inputs["orders"].append(duplicate_order)
    elif break_class is BreakClass.DUPLICATE_BANK_CREDIT:
        for bank_transaction in raw_inputs["bank_transactions"]:
            if bank_transaction["utr"] == scenario_settlement_utr:
                duplicate_bank_transaction = dict(bank_transaction)
                duplicate_bank_transaction["bank_transaction_id"] = (
                    f"duplicate_{bank_transaction['bank_transaction_id']}"
                )
                raw_inputs["bank_transactions"].append(duplicate_bank_transaction)
                break
    elif break_class is BreakClass.DISPUTE_ADJUSTMENT:
        adjustment = _adjustment_row(
            entity_id=f"dispute_adjustment_{case_number:03d}",
            payment_row=target_row,
            amount_paise=500,
            dispute_id=f"disp_{case_number:03d}",
        )
        reconciliation_rows.append(adjustment)
        return _require_string(adjustment, "entity_id")
    elif break_class is BreakClass.GENERAL_ADJUSTMENT:
        adjustment = _adjustment_row(
            entity_id=f"general_adjustment_{case_number:03d}",
            payment_row=target_row,
            amount_paise=700,
            dispute_id=None,
        )
        reconciliation_rows.append(adjustment)
        return _require_string(adjustment, "entity_id")
    elif break_class is BreakClass.MISSING_ORDER:
        raw_inputs["orders"] = [
            order for order in raw_inputs["orders"] if order["order_id"] != target_row["order_id"]
        ]
    elif break_class is BreakClass.MISSING_PAYMENT:
        raw_inputs["payments"] = [
            payment
            for payment in raw_inputs["payments"]
            if payment["payment_id"] != target_row["payment_id"]
        ]
    elif break_class is BreakClass.MISSING_SETTLEMENT:
        _remove_settlement_bank_evidence(raw_inputs, scenario_settlement_utr)
        target_row["settlement_id"] = None
        target_row["settlement_utr"] = None
        target_row["settled"] = False
    elif break_class is BreakClass.MISSING_BANK_CREDIT:
        _remove_settlement_bank_evidence(raw_inputs, scenario_settlement_utr)
    elif break_class is BreakClass.UNRESOLVABLE:
        original_order_id = target_row["order_id"]
        original_payment_id = target_row["payment_id"]
        _remove_settlement_bank_evidence(raw_inputs, scenario_settlement_utr)
        raw_inputs["orders"] = [
            order for order in raw_inputs["orders"] if order["order_id"] != original_order_id
        ]
        raw_inputs["payments"] = [
            payment
            for payment in raw_inputs["payments"]
            if payment["payment_id"] != original_payment_id
        ]
        target_row["order_id"] = None
        target_row["order_receipt"] = None
        target_row["payment_id"] = None
        target_row["settlement_id"] = None
        target_row["settlement_utr"] = None
    else:
        raise ValueError(f"unsupported scenario {break_class.value}")

    return target_entity_id


def _has_intentional_bank_evidence_break(break_class: BreakClass) -> bool:
    return break_class in {
        BreakClass.DUPLICATE_BANK_CREDIT,
        BreakClass.MISSING_BANK_CREDIT,
        BreakClass.MISSING_SETTLEMENT,
        BreakClass.UNRESOLVABLE,
        BreakClass.MANGLED_NARRATION,
        BreakClass.MANGLED_UTR,
    }


def generate_messy_dataset(seed: int, profile: ScenarioDistribution) -> GeneratedDataset:
    requested_case_count = sum(profile.scenario_counts.values())
    record_count = max(profile.base_record_count, requested_case_count)
    orders, payments = generate_orders_and_payments(seed=seed, record_count=record_count)
    reconciliation_rows = generate_reconciliation_rows(orders=orders, payments=payments)
    raw_inputs: dict[str, list[RawRecord]] = {
        "orders": orders,
        "payments": payments,
        "reconciliation_rows": reconciliation_rows,
        "bank_transactions": generate_bank_transactions(reconciliation_rows),
    }
    truth_cases: list[dict[str, Any]] = []
    case_number = 0
    for break_class in sorted(profile.scenario_counts, key=lambda value: value.value):
        for occurrence in range(profile.scenario_counts[break_class]):
            target_row = reconciliation_rows[case_number]
            scenario_settlement_utr = _isolate_scenario_settlement(
                raw_inputs, target_row, case_number
            )
            raw_entity_id = _inject_scenario(
                break_class,
                case_number,
                raw_inputs,
                target_row,
                scenario_settlement_utr,
            )
            if not _has_intentional_bank_evidence_break(break_class):
                _recompute_settlement_bank_evidence(
                    raw_inputs,
                    scenario_settlement_utr,
                    f"bank_scenario_{case_number:03d}",
                )
            truth_cases.append(
                create_ground_truth_case(
                    case_id=f"case_{break_class.value.lower()}_{occurrence:03d}",
                    break_class=break_class,
                    raw_entity_ids=[raw_entity_id],
                )
            )
            case_number += 1

    canonical_raw_input_content = dumps(
        raw_inputs, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return GeneratedDataset(
        raw_inputs=raw_inputs,
        input_hash=sha256(canonical_raw_input_content).hexdigest(),
        ground_truth=create_ground_truth(truth_cases),
    )
