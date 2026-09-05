from __future__ import annotations

from io import BytesIO

import pdfplumber

from .validation import ImportValidationError, ParsedTable, safe_cell


def inspect_pdf(filename: str, content: bytes) -> ParsedTable:
    try:
        with pdfplumber.open(BytesIO(content)) as document:
            tables = [table for page in document.pages for table in page.extract_tables()]
    except Exception as error:
        raise ImportValidationError("PDF_TEXT_TABLE_REQUIRED") from error
    if not tables or not tables[0] or len(tables[0]) < 2:
        raise ImportValidationError("PDF_TEXT_TABLE_REQUIRED")
    headers = tuple(safe_cell(value).strip() for value in tables[0][0])
    if not all(headers):
        raise ImportValidationError("PDF_TEXT_TABLE_REQUIRED")
    rows = tuple(
        {header: safe_cell(value) for header, value in zip(headers, row, strict=True)}
        for row in tables[0][1:]
    )
    return ParsedTable(filename, "pdf", headers, rows)
