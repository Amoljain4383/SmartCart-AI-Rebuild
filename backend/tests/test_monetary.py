"""Tests for integer paise monetary representation and financial precision."""
from decimal import Decimal
import pytest
from app.core.currency import (
    rupees_to_paise,
    paise_to_decimal,
    paise_to_rupees_str,
    compute_landed_cost_paise,
)


def test_rupees_to_paise_exact():
    """Verify conversion from rupees (int, float str, Decimal) to integer paise."""
    assert rupees_to_paise(100) == 10000
    assert rupees_to_paise("499.50") == 49950
    assert rupees_to_paise("0.99") == 99
    assert rupees_to_paise(Decimal("12999.00")) == 1299900
    assert isinstance(rupees_to_paise("19.99"), int)


def test_no_floating_point_imprecision():
    """Classic floating point trap: 0.1 + 0.2 != 0.3 in IEEE 754 floats.

    Integer paise guarantees exactness: 10 paise + 20 paise == 30 paise.
    """
    amount_a_paise = rupees_to_paise("0.10")  # 10 paise
    amount_b_paise = rupees_to_paise("0.20")  # 20 paise
    total_paise = amount_a_paise + amount_b_paise

    assert total_paise == 30
    assert paise_to_decimal(total_paise) == Decimal("0.30")


def test_paise_to_decimal():
    """Verify paise to Decimal conversion retains exact scale."""
    dec = paise_to_decimal(1299900)
    assert dec == Decimal("12999.00")
    assert str(dec) == "12999.00"

    with pytest.raises(TypeError):
        paise_to_decimal(1299.5)  # Must be strictly integer


def test_paise_to_rupees_str():
    """Verify INR formatting with thousands separators and optional currency symbol."""
    assert paise_to_rupees_str(1299900) == "₹12,999.00"
    assert paise_to_rupees_str(1299900, include_symbol=False) == "12,999.00"
    assert paise_to_rupees_str(50) == "₹0.50"
    assert paise_to_rupees_str(0) == "₹0.00"


def test_compute_landed_cost_paise():
    """Verify landed cost calculation adds price and shipping in integer paise."""
    product_price_paise = 2599900  # ₹25,999.00
    shipping_cost_paise = 49900    # ₹499.00
    landed_cost = compute_landed_cost_paise(product_price_paise, shipping_cost_paise)

    assert landed_cost == 2649800
    assert paise_to_rupees_str(landed_cost) == "₹26,498.00"


def test_compute_landed_cost_negative_rejection():
    """Verify negative monetary inputs are strictly rejected."""
    with pytest.raises(ValueError, match="product_price_paise cannot be negative"):
        compute_landed_cost_paise(-100, 50)

    with pytest.raises(ValueError, match="shipping_cost_paise cannot be negative"):
        compute_landed_cost_paise(100, -50)
