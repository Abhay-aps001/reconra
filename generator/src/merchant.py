from __future__ import annotations

from datetime import UTC, datetime, timedelta
from random import Random

RawRecord = dict[str, object]


def generate_orders_and_payments(
    seed: int, record_count: int
) -> tuple[list[RawRecord], list[RawRecord]]:
    random = Random(seed)
    orders: list[RawRecord] = []
    payments: list[RawRecord] = []
    start = datetime(2026, 1, 1, 10, 0, tzinfo=UTC)
    methods = ("upi", "card", "card", "netbanking", "wallet")

    for index in range(record_count):
        created_at = start + timedelta(days=index % 14, minutes=index * 11)
        captured_at = created_at + timedelta(minutes=5)
        amount_paise = random.randrange(499, 15_000) * 100
        order_id = f"order_clean_{index:03d}"
        payment_id = f"pay_clean_{index:03d}"
        receipt = f"NIVARA-CLEAN-{index:03d}"
        method = methods[index % len(methods)]
        if method == "card":
            card_type = "credit" if index % 2 else "debit"
            card_network = "Visa" if card_type == "credit" else "RuPay"
            card_issuer = "HDFC Bank" if card_type == "credit" else "ICICI Bank"
        else:
            card_type = None
            card_network = None
            card_issuer = None

        orders.append(
            {
                "order_id": order_id,
                "receipt": receipt,
                "created_at": created_at.isoformat(),
                "amount_paise": amount_paise,
                "currency": "INR",
                "status": "paid",
            }
        )
        payments.append(
            {
                "payment_id": payment_id,
                "order_id": order_id,
                "amount_paise": amount_paise,
                "currency": "INR",
                "method": method,
                "captured_at": captured_at.isoformat(),
                "status": "captured",
                "card_type": card_type,
                "card_network": card_network,
                "card_issuer": card_issuer,
            }
        )

    return orders, payments
