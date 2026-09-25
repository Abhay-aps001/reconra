"""Integer-only paise presentation helpers for external artifacts."""


def display_paise(value: int) -> str:
    if type(value) is not int:
        raise TypeError("paise display requires an integer")
    sign = "-" if value < 0 else ""
    absolute = abs(value)
    rupees, paise = divmod(absolute, 100)
    return f"{sign}{rupees:,}.{paise:02d}"


def escape_csv_text(value: str) -> str:
    """Keep untrusted text cells inert when opened by spreadsheet software."""
    return f"'{value}" if value.startswith(("=", "+", "-", "@")) else value
