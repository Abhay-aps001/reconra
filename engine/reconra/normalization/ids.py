"""Conservative normalization for identifiers and UTR references."""

_UTR_FORMATTING_SEPARATORS = frozenset(" \t\r\n-/_.")


def normalize_identifier(value: str | None) -> str | None:
    """Trim and uppercase an identifier without changing internal evidence."""
    if value is None:
        return None

    normalized = value.strip()
    if not normalized:
        return None
    return normalized.upper()


def normalize_utr(value: str | None) -> str | None:
    """Uppercase a UTR and remove only known formatting separators."""
    if value is None:
        return None

    trimmed = value.strip()
    if not trimmed:
        return None

    normalized = "".join(
        character for character in trimmed.upper() if character not in _UTR_FORMATTING_SEPARATORS
    )
    return normalized or None
