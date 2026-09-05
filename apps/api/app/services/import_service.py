from __future__ import annotations

from pathlib import PurePath
from typing import cast
from uuid import uuid4

from app.services.import_store import ImportStore
from app.services.reconciliation_service import reconcile_inputs
from fastapi import UploadFile
from reconra.ingestion.csv import inspect_csv
from reconra.ingestion.mapping import suggest_column_mappings
from reconra.ingestion.pdf import inspect_pdf
from reconra.ingestion.validation import ImportValidationError, ParsedTable, parse_paise
from reconra.ingestion.xlsx import inspect_xlsx
from reconra.reconciliation.pipeline import CanonicalDataset

import_store = ImportStore()
_LIMIT = 10 * 1024 * 1024
_COMBINED_LIMIT = 25 * 1024 * 1024
_ROW_LIMIT = 10_000
_ROLE_FUZZY_MIN_CONFIDENCE = 0.86
_SCHEMAS = {
    "bank_transactions": ("transaction_date", "description", "credit_paise", "utr"),
    "orders": ("order_id", "created_at", "amount_paise", "status"),
    "payments": ("payment_id", "order_id", "amount_paise", "status"),
    "reconciliation_rows": (
        "entity_id",
        "entry_type",
        "credit_paise",
        "debit_paise",
        "amount_paise",
        "created_at",
    ),
}


class ImportServiceError(Exception):
    def __init__(self, code: str, status_code: int = 400) -> None:
        self.code = code
        self.status_code = status_code


async def inspect_import(files: list[UploadFile]) -> dict[str, object]:
    total = 0
    tables: list[ParsedTable] = []
    for file in files:
        filename = file.filename or ""
        _safe_filename(filename)
        content = await file.read()
        total += len(content)
        if len(content) > _LIMIT:
            raise ImportServiceError("FILE_TOO_LARGE")
        if total > _COMBINED_LIMIT:
            raise ImportServiceError("COMBINED_SIZE_TOO_LARGE")
        tables.append(_parse(filename, content))
    if sum(len(table.rows) for table in tables) > _ROW_LIMIT:
        raise ImportServiceError("ROW_LIMIT_EXCEEDED")
    import_id = f"import_{uuid4().hex[:20]}"
    stored = {"tables": tables, "mappings": None}
    import_store.put(import_id, stored)
    return _inspection(import_id, tables)


def validate_import(import_id: str, mappings: dict[str, dict[str, str]]) -> dict[str, object]:
    stored = _stored(import_id)
    tables = _tables(stored)
    for table in tables:
        mapping = mappings.get(table.filename)
        if mapping is None:
            raise ImportServiceError("MAPPING_REQUIRED")
        if set(mapping) - set(table.columns) or len(set(mapping.values())) != len(mapping):
            raise ImportServiceError("INVALID_MAPPING")
        role = _role(table.columns)
        required = set(_SCHEMAS[role])
        if not required <= set(mapping.values()):
            raise ImportServiceError("REQUIRED_FIELD_MISSING")
        for row in table.rows:
            _canonical_row(import_id, table.filename, role, row, mapping, len(table.rows))
    stored["mappings"] = mappings
    return {"import_id": import_id, "validated": True}


def reconcile_import(import_id: str) -> dict[str, object]:
    stored = _stored(import_id)
    mappings = stored["mappings"]
    if not isinstance(mappings, dict):
        raise ImportServiceError("IMPORT_NOT_VALIDATED", 409)
    raw: dict[str, list[dict[str, object]]] = {
        "orders": [],
        "payments": [],
        "reconciliation_rows": [],
        "bank_transactions": [],
    }
    for table in _tables(stored):
        role = _role(table.columns)
        for index, row in enumerate(table.rows):
            mapping = mappings[table.filename]
            raw[role].append(
                _canonical_row(import_id, table.filename, role, row, mapping, index)
            )
    return reconcile_inputs(cast(dict[str, object], raw))


def _parse(filename: str, content: bytes) -> ParsedTable:
    suffix = PurePath(filename).suffix.lower()
    try:
        if suffix == ".csv":
            return inspect_csv(filename, content)
        if suffix == ".xlsx":
            return inspect_xlsx(filename, content)
        if suffix == ".pdf":
            return inspect_pdf(filename, content)
    except ImportValidationError as error:
        raise ImportServiceError(error.code) from error
    raise ImportServiceError("UNSUPPORTED_FILE_TYPE")


def _safe_filename(filename: str) -> None:
    if not filename or PurePath(filename).name != filename or "/" in filename or "\\" in filename:
        raise ImportServiceError("INVALID_FILENAME")


def _role(columns: tuple[str, ...]) -> str:
    scores = {role: _role_score(columns, schema) for role, schema in _SCHEMAS.items()}
    evidence = {role: score for role, score in scores.items() if score != (0, 0, 0)}
    if not evidence:
        raise ImportServiceError("AMBIGUOUS_SOURCE_ROLE")
    highest = max(evidence.values())
    winners = [role for role, score in evidence.items() if score == highest]
    if len(winners) != 1:
        raise ImportServiceError("AMBIGUOUS_SOURCE_ROLE")
    return winners[0]


def _role_score(columns: tuple[str, ...], schema: tuple[str, ...]) -> tuple[int, int, int]:
    exact = 0
    token = 0
    fuzzy = 0
    for suggestion in suggest_column_mappings(columns, schema):
        if suggestion.reason == "exact_alias":
            exact += 1
        elif suggestion.reason == "token_match":
            token += 1
        elif suggestion.confidence >= _ROLE_FUZZY_MIN_CONFIDENCE:
            fuzzy += round(suggestion.confidence * 100)
    return exact, token, fuzzy


def _canonical_row(
    import_id: str,
    filename: str,
    role: str,
    row: dict[str, str],
    mapping: dict[str, str],
    index: int,
) -> dict[str, object]:
    mapped: dict[str, object] = {target: row[source] for source, target in mapping.items()}
    try:
        for key in list(mapped):
            if key.endswith("_paise"):
                mapped[key] = parse_paise(mapped[key])
        if role == "bank_transactions":
            mapped.setdefault("bank_transaction_id", f"{import_id}:{filename}:{index}")
            mapped.setdefault("debit_paise", 0)
        if role == "reconciliation_rows":
            mapped.setdefault("fee_paise", 0)
            mapped.setdefault("tax_paise", 0)
        raw: dict[str, list[dict[str, object]]] = {
            "orders": [],
            "payments": [],
            "reconciliation_rows": [],
            "bank_transactions": [],
        }
        raw[role].append(mapped)
        CanonicalDataset.from_raw_inputs(cast(dict[str, object], raw)).validate()
    except (ImportValidationError, TypeError, ValueError) as error:
        raise ImportServiceError("INVALID_MAPPING_VALUE") from error
    return mapped


def _stored(import_id: str) -> dict[str, object]:
    stored = import_store.get(import_id)
    if stored is None:
        raise ImportServiceError("IMPORT_NOT_FOUND", 404)
    return stored


def _tables(stored: dict[str, object]) -> list[ParsedTable]:
    tables = stored.get("tables")
    if not isinstance(tables, list) or not all(isinstance(table, ParsedTable) for table in tables):
        raise RuntimeError("stored import has invalid parsed tables")
    return tables


def _inspection(import_id: str, tables: list[ParsedTable]) -> dict[str, object]:
    return {
        "import_id": import_id,
        "files": [
            {
                "filename": table.filename,
                "source_type": table.source_type,
                "columns": list(table.columns),
                "row_count": len(table.rows),
                "sample_rows": [dict(row) for row in table.rows[:5]],
                "candidate_role": _role(table.columns),
                "suggestions": [
                    item.__dict__
                    for item in suggest_column_mappings(
                        table.columns, _SCHEMAS[_role(table.columns)]
                    )
                ],
            }
            for table in tables
        ],
        "warnings": [],
    }
