from __future__ import annotations

import re

from rapidfuzz.fuzz import ratio

from .validation import ColumnSuggestion

_ALIASES = {
    "transaction_date": {"txn date", "transaction date", "date"},
    "description": {"narration", "description", "remarks"},
    "credit_paise": {"deposit amt", "credit amount", "credit", "amount"},
    "debit_paise": {"debit amount", "debit", "withdrawal amt"},
    "utr": {"ref no", "utr", "reference"},
    "order_id": {"order id", "order"},
    "payment_id": {"payment id", "payment"},
    "bank_transaction_id": {"transaction id", "bank transaction id", "txn id"},
    "created_at": {"created at", "created date"},
    "amount_paise": {"amount", "amount paid"},
    "status": {"status"},
    "entity_id": {"entity id"},
    "entry_type": {"entry type", "type"},
}


def suggest_column_mappings(
    columns: list[str] | tuple[str, ...], target_schema: tuple[str, ...]
) -> list[ColumnSuggestion]:
    suggestions: list[ColumnSuggestion] = []
    for column in columns:
        normalized = _normalize(column)
        exact = next(
            (field for field in target_schema if normalized in _ALIASES.get(field, set())), None
        )
        if exact is not None:
            suggestions.append(ColumnSuggestion(column, exact, 1.0, "exact_alias"))
            continue
        tokens = set(normalized.split())
        token = next((field for field in target_schema if tokens & set(field.split("_"))), None)
        if token is not None:
            suggestions.append(ColumnSuggestion(column, token, 0.8, "token_match"))
            continue
        candidate, score = max(
            ((field, ratio(normalized, _normalize(field))) for field in target_schema),
            key=lambda item: item[1],
        )
        suggestions.append(ColumnSuggestion(column, candidate, score / 100, "rapidfuzz"))
    return suggestions


def _normalize(value: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())
