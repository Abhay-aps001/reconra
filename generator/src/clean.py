from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from json import dumps
from typing import Any

from .bank import generate_bank_transactions
from .merchant import RawRecord, generate_orders_and_payments
from .razorpay_recon import generate_reconciliation_rows


@dataclass(frozen=True)
class GeneratedDataset:
    raw_inputs: dict[str, list[RawRecord]]
    input_hash: str
    ground_truth: dict[str, list[dict[str, Any]]] | None = None


def generate_clean_dataset(seed: int) -> GeneratedDataset:
    orders, payments = generate_orders_and_payments(seed=seed, record_count=64)
    reconciliation_rows = generate_reconciliation_rows(orders=orders, payments=payments)
    bank_transactions = generate_bank_transactions(reconciliation_rows)
    raw_inputs: dict[str, list[RawRecord]] = {
        "orders": orders,
        "payments": payments,
        "reconciliation_rows": reconciliation_rows,
        "bank_transactions": bank_transactions,
    }
    canonical_raw_input_content = dumps(
        raw_inputs, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return GeneratedDataset(
        raw_inputs=raw_inputs,
        input_hash=sha256(canonical_raw_input_content).hexdigest(),
    )
