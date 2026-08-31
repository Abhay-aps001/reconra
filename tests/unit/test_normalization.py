"""Tests for conservative, deterministic normalization helpers."""

from datetime import date

import pytest
from reconra.normalization.dates import date_distance_days
from reconra.normalization.ids import normalize_identifier, normalize_utr
from reconra.normalization.text import normalize_narration


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, None),
        ("", None),
        (" \t\n ", None),
        ("  pay_AbC-19  ", "PAY_ABC-19"),
        ("\t  order_42 \n", "ORDER_42"),
        ("PAY_ABC-19", "PAY_ABC-19"),
        ("ab  /- 12", "AB  /- 12"),
    ],
)
def test_normalize_identifier_standardizes_only_existing_evidence(
    value: str | None, expected: str | None
) -> None:
    assert normalize_identifier(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, None),
        ("", None),
        (" \t ", None),
        (" utr-ab/12.3_4 ", "UTRAB1234"),
        ("rZp- 8/9.0", "RZP890"),
        ("UTRABC123", "UTRABC123"),
        ("UTR-AB12", "UTRAB12"),
    ],
)
def test_normalize_utr_removes_only_formatting_separators(
    value: str | None, expected: str | None
) -> None:
    assert normalize_utr(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, ""),
        ("", ""),
        (" \t\n ", ""),
        ("  UPI / RZP-ABC  ", "upi / rzp-abc"),
        ("Bank   credit\t\tRZP-12", "bank credit rzp-12"),
        ("RZP SETTL...", "rzp settl..."),
        ("NEFT: RZP/ABC-12!", "neft: rzp/abc-12!"),
    ],
)
def test_normalize_narration_preserves_words_and_punctuation(
    value: str | None, expected: str
) -> None:
    assert normalize_narration(value) == expected


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (date(2026, 8, 31), date(2026, 8, 31), 0),
        (date(2026, 8, 31), date(2026, 9, 1), 1),
        (date(2026, 9, 1), date(2026, 8, 31), 1),
        (date(2026, 1, 31), date(2026, 2, 1), 1),
        (date(2025, 12, 31), date(2026, 1, 1), 1),
        (date(2024, 2, 28), date(2024, 3, 1), 2),
    ],
)
def test_date_distance_days_returns_absolute_calendar_distance(
    a: date, b: date, expected: int
) -> None:
    assert date_distance_days(a, b) == expected


@pytest.mark.parametrize(
    ("normalizer", "value"),
    [
        (normalize_identifier, "  pay_AbC-19  "),
        (normalize_utr, " utr-ab/12.3_4 "),
        (normalize_narration, "Bank   credit\t\tRZP-12"),
    ],
)
def test_text_normalizers_are_deterministic(normalizer: object, value: str) -> None:
    assert callable(normalizer)
    assert normalizer(value) == normalizer(value)


def test_date_distance_days_is_deterministic() -> None:
    first = date_distance_days(date(2024, 2, 28), date(2024, 3, 1))
    second = date_distance_days(date(2024, 2, 28), date(2024, 3, 1))
    assert first == second == 2
