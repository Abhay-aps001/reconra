"""Fuzzy evidence scoring for damaged identifiers and narrations."""

from rapidfuzz import fuzz
from reconra.normalization.ids import normalize_utr
from reconra.normalization.text import normalize_narration


def score_utr_similarity(a: str, b: str) -> float:
    """Return normalized UTR similarity in the inclusive range zero to one."""
    normalized_a = normalize_utr(a)
    normalized_b = normalize_utr(b)
    if normalized_a is None or normalized_b is None:
        return 0.0
    return fuzz.ratio(normalized_a, normalized_b) / 100


def score_narration_similarity(a: str, b: str) -> float:
    """Return normalized narration similarity in the inclusive range zero to one."""
    normalized_a = normalize_narration(a)
    normalized_b = normalize_narration(b)
    if not normalized_a or not normalized_b:
        return 0.0
    return fuzz.token_set_ratio(normalized_a, normalized_b) / 100
