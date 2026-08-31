"""Conservative normalization for free-form narration evidence."""


def normalize_narration(value: str | None) -> str:
    """Lowercase and standardize whitespace while retaining textual evidence."""
    if value is None:
        return ""
    return " ".join(value.split()).lower()
