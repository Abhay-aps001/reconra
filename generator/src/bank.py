from __future__ import annotations

from .merchant import RawRecord


def settlement_net_paise(reconciliation_rows: list[RawRecord]) -> int:
    """Return the signed bank settlement amount from raw reconciliation evidence."""
    net_paise = 0
    for row in reconciliation_rows:
        values: dict[str, int] = {}
        for field_name in ("credit", "debit", "fee", "tax"):
            value = row[field_name]
            if type(value) is not int:
                raise TypeError(f"reconciliation {field_name} must be an integer")
            values[field_name] = value
        net_paise += values["credit"] - values["debit"] - values["fee"] - values["tax"]
    return net_paise


def bank_transaction_for_settlement(
    reconciliation_rows: list[RawRecord], bank_transaction_id: str
) -> RawRecord:
    if not reconciliation_rows:
        raise ValueError("settlement bank evidence requires at least one reconciliation row")

    first_row = reconciliation_rows[0]
    settled_at = first_row["settled_at"]
    if not isinstance(settled_at, str):
        raise TypeError("settled_at must be an ISO timestamp")
    settlement_id = first_row["settlement_id"]
    if not isinstance(settlement_id, str):
        raise TypeError("settlement_id must be a string")
    settlement_utr = first_row["settlement_utr"]
    if not isinstance(settlement_utr, str):
        raise TypeError("settlement_utr must be a string")
    if any(row["settlement_id"] != settlement_id for row in reconciliation_rows):
        raise ValueError("settlement rows must share one settlement_id")
    if any(row["settlement_utr"] != settlement_utr for row in reconciliation_rows):
        raise ValueError("settlement rows must share one settlement_utr")

    net_paise = settlement_net_paise(reconciliation_rows)
    settlement_date = settled_at.split("T", maxsplit=1)[0]
    return {
        "bank_transaction_id": bank_transaction_id,
        "transaction_date": settlement_date,
        "value_date": settlement_date,
        "description": f"Razorpay settlement {settlement_id}",
        "reference": settlement_utr,
        "utr": settlement_utr,
        "credit_paise": max(net_paise, 0),
        "debit_paise": max(-net_paise, 0),
    }


def generate_bank_transactions(reconciliation_rows: list[RawRecord]) -> list[RawRecord]:
    rows_by_settlement_utr: dict[str, list[RawRecord]] = {}
    for row in reconciliation_rows:
        settlement_utr = row["settlement_utr"]
        if not isinstance(settlement_utr, str):
            raise TypeError("settlement_utr must be a string")
        rows_by_settlement_utr.setdefault(settlement_utr, []).append(row)

    bank_transactions: list[RawRecord] = []
    for index, (_settlement_utr, settlement_rows) in enumerate(rows_by_settlement_utr.items()):
        bank_transactions.append(
            bank_transaction_for_settlement(
                settlement_rows, bank_transaction_id=f"bank_clean_{index:03d}"
            )
        )

    return bank_transactions
