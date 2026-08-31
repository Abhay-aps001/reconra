from decimal import Decimal, InvalidOperation

Paise = int


def parse_rupees_to_paise(value: str | Decimal | int) -> Paise:
    """Convert an exact rupee boundary value to paise without rounding."""
    if isinstance(value, float):
        raise TypeError("float monetary input is not permitted")
    if isinstance(value, bool) or not isinstance(value, (str, Decimal, int)):
        raise TypeError("monetary input must be str, Decimal, or int")
    try:
        rupees = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("invalid rupee value") from exc
    if not rupees.is_finite():
        raise ValueError("rupee value must be finite")
    paise = rupees * 100
    if paise != paise.to_integral_value():
        raise ValueError("rupee value has precision beyond paise")
    return int(paise)


def format_paise_inr(value: Paise) -> str:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("paise value must be int")
    sign = "-" if value < 0 else ""
    amount = abs(value)
    rupees, paise = divmod(amount, 100)
    digits = str(rupees)
    if len(digits) > 3:
        head, tail = digits[:-3], digits[-3:]
        groups: list[str] = []
        while head:
            groups.append(head[-2:])
            head = head[:-2]
        digits = ",".join(reversed(groups)) + "," + tail
    return f"{sign}₹{digits}.{paise:02d}"
