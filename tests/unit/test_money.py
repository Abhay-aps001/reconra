from decimal import Decimal

import pytest
from reconra.models.money import format_paise_inr, parse_rupees_to_paise


def test_parse_rupees_exactly() -> None:
    assert parse_rupees_to_paise("2749.50") == 274950
    assert parse_rupees_to_paise(Decimal("0.01")) == 1


def test_no_float_input() -> None:
    with pytest.raises(TypeError):
        parse_rupees_to_paise(2749.50)


def test_bool_money_inputs_are_rejected() -> None:
    with pytest.raises(TypeError):
        parse_rupees_to_paise(True)
    with pytest.raises(TypeError):
        format_paise_inr(False)


def test_indian_formatting() -> None:
    assert format_paise_inr(528419000) == "₹52,84,190.00"
    assert format_paise_inr(-1) == "-₹0.01"
    assert format_paise_inr(0) == "₹0.00"
    assert format_paise_inr(10**18) == "₹10,00,00,00,00,00,00,000.00"


def test_excess_precision_is_rejected() -> None:
    with pytest.raises(ValueError):
        parse_rupees_to_paise("1.001")
