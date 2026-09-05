from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from reconra.models.money import parse_rupees_to_paise


class ImportValidationError(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class ParsedTable:
    filename: str
    source_type: str
    columns: tuple[str, ...]
    rows: tuple[dict[str, str], ...]


@dataclass(frozen=True)
class ColumnSuggestion:
    source_column: str
    target_field: str
    confidence: float
    reason: str


def parse_paise(value: object) -> int:
    if isinstance(value, float):
        raise ImportValidationError("INVALID_MONEY")
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        raise ImportValidationError("INVALID_MONEY")
    normalized = value.replace(",", "") if isinstance(value, str) else value
    try:
        return parse_rupees_to_paise(normalized)
    except (TypeError, ValueError, InvalidOperation) as error:
        raise ImportValidationError("INVALID_MONEY") from error


def safe_cell(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    return text[:160]
