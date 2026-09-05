from __future__ import annotations

from io import BytesIO

import pytest
from app.services.import_service import ImportServiceError, _role
from reconra.ingestion.csv import inspect_csv
from reconra.ingestion.mapping import suggest_column_mappings
from reconra.ingestion.validation import ImportValidationError, parse_paise
from reconra.ingestion.xlsx import inspect_xlsx


def test_csv_preserves_ids_dates_and_indian_money_as_integer_paise() -> None:
    table = inspect_csv(
        "bank.csv",
        b'Txn Date,Narration,Deposit Amt,Ref No\n2026-09-01,Settlement,"1,23,456.78",UTR-1\n',
    )
    assert table.columns == ("Txn Date", "Narration", "Deposit Amt", "Ref No")
    assert parse_paise("1,23,456.78") == 12_345_678
    assert type(parse_paise("123.45")) is int


def test_money_parser_rejects_float_and_precision_beyond_paise() -> None:
    with pytest.raises(ImportValidationError, match="INVALID_MONEY"):
        parse_paise("12.345")
    with pytest.raises(ImportValidationError, match="INVALID_MONEY"):
        parse_paise(12.34)


def test_xlsx_inspection_preserves_text_identifiers_and_dates() -> None:
    from openpyxl import Workbook

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(["Order ID", "Created At", "Amount", "Status"])
    worksheet.append(["000123", "2026-09-01T00:00:00+00:00", "123.45", "paid"])
    stream = BytesIO()
    workbook.save(stream)

    table = inspect_xlsx("orders.xlsx", stream.getvalue())
    assert table.rows[0]["Order ID"] == "000123"


def test_deterministic_mapping_prefers_alias_then_token_then_fuzzy() -> None:
    suggestions = suggest_column_mappings(
        ["Txn Date", "Narration", "Deposit Amt", "Ref No", "trnsctn dt"],
        ("transaction_date", "description", "credit_paise", "utr"),
    )
    by_source = {suggestion.source_column: suggestion for suggestion in suggestions}
    assert by_source["Txn Date"].target_field == "transaction_date"
    assert by_source["Txn Date"].reason == "exact_alias"
    assert by_source["Narration"].target_field == "description"
    assert by_source["Deposit Amt"].target_field == "credit_paise"
    assert by_source["trnsctn dt"].reason == "rapidfuzz"


@pytest.mark.parametrize(
    ("columns", "expected"),
    [
        (("Txn Date", "Narration", "Deposit Amt", "Ref No"), "bank_transactions"),
        (("Order ID", "Created At", "Amount", "Status"), "orders"),
        (("Payment ID", "Order ID", "Amount", "Status"), "payments"),
        (
            ("Entity ID", "Entry Type", "Credit", "Debit", "Amount", "Created At"),
            "reconciliation_rows",
        ),
    ],
)
def test_role_classification_uses_genuine_schema_evidence(
    columns: tuple[str, ...], expected: str
) -> None:
    assert _role(columns) == expected


@pytest.mark.parametrize("columns", [("completely unrelated",), ("Amount", "Status")])
def test_weak_or_equal_role_evidence_is_rejected_safely(columns: tuple[str, ...]) -> None:
    with pytest.raises(ImportServiceError, match="AMBIGUOUS_SOURCE_ROLE"):
        _role(columns)
