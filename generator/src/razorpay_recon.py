from __future__ import annotations

from datetime import UTC, datetime, timedelta

from .merchant import RawRecord


def generate_reconciliation_rows(
    orders: list[RawRecord], payments: list[RawRecord]
) -> list[RawRecord]:
    reconciliation_rows: list[RawRecord] = []
    settlement_start = datetime(2026, 1, 20, 12, 0, tzinfo=UTC)

    for index, (order, payment) in enumerate(zip(orders, payments, strict=True)):
        settlement_number = index // 8
        amount_paise = payment["amount_paise"]
        if type(amount_paise) is not int:
            raise TypeError("payment amount_paise must be an integer")
        settlement_id = f"setl_clean_{settlement_number:03d}"
        settlement_utr = f"UTR-CLEAN-{settlement_number:03d}"
        settled_at = settlement_start + timedelta(days=settlement_number)

        reconciliation_rows.append(
            {
                "entity_id": f"recon_clean_{index:03d}",
                "type": "payment",
                "debit": 0,
                "credit": amount_paise,
                "amount": amount_paise,
                "currency": "INR",
                "fee": 0,
                "tax": 0,
                "on_hold": False,
                "settled": True,
                "created_at": payment["captured_at"],
                "settled_at": settled_at.isoformat(),
                "settlement_id": settlement_id,
                "description": "Captured payment",
                "notes": "Nivara clean fixture",
                "payment_id": payment["payment_id"],
                "settlement_utr": settlement_utr,
                "order_id": order["order_id"],
                "order_receipt": order["receipt"],
                "method": payment["method"],
                "card_network": payment["card_network"],
                "card_issuer": payment["card_issuer"],
                "card_type": payment["card_type"],
                "dispute_id": None,
            }
        )

    return reconciliation_rows
