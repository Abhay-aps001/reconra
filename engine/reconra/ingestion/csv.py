from __future__ import annotations

import csv
from io import StringIO

from .validation import ImportValidationError, ParsedTable, safe_cell


def inspect_csv(filename: str, content: bytes) -> ParsedTable:
    try:
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(StringIO(text), strict=True)
        if not reader.fieldnames or any(
            not field or not field.strip() for field in reader.fieldnames
        ):
            raise ImportValidationError("MALFORMED_CSV")
        rows: list[dict[str, str]] = []
        for row in reader:
            if None in row:
                raise ImportValidationError("MALFORMED_CSV")
            rows.append({field: safe_cell(row[field]) for field in reader.fieldnames})
    except (csv.Error, UnicodeDecodeError, KeyError) as error:
        raise ImportValidationError("MALFORMED_CSV") from error
    return ParsedTable(filename, "csv", tuple(reader.fieldnames), tuple(rows))
