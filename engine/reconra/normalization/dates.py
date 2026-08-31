"""Date-only normalization helpers."""

from datetime import date


def date_distance_days(a: date, b: date) -> int:
    """Return the absolute number of calendar days between two dates."""
    return abs((a - b).days)
