"""Financial and currency calculation utilities.

All internal financial values are strictly represented and calculated as
integer paise (1 INR = 100 paise) to avoid any floating-point arithmetic drift.
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Union, Optional


def rupees_to_paise(amount: Union[int, str, Decimal]) -> int:
    """Convert an amount in INR rupees to integer paise.

    Example:
        rupees_to_paise("499.50") -> 49950
        rupees_to_paise(499) -> 49900
        rupees_to_paise(Decimal("12.99")) -> 1299
    """
    if isinstance(amount, int):
        return amount * 100

    dec = Decimal(str(amount))
    paise_dec = (dec * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(paise_dec)


def paise_to_decimal(paise: int) -> Decimal:
    """Convert integer paise to a two-decimal-place Decimal in INR rupees.

    Example:
        paise_to_decimal(49950) -> Decimal("499.50")
    """
    if not isinstance(paise, int):
        raise TypeError(f"paise must be an integer, received {type(paise).__name__}")
    return (Decimal(paise) / Decimal(100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def paise_to_rupees_str(paise: int, include_symbol: bool = True) -> str:
    """Format integer paise into a standard INR currency string.

    Example:
        paise_to_rupees_str(1299900) -> "₹12,999.00"
    """
    dec = paise_to_decimal(paise)
    formatted = f"{dec:,.2f}"
    return f"₹{formatted}" if include_symbol else formatted


def paise_to_paypal_amount_str(paise: int) -> str:
    """Format integer paise into PayPal's required two-decimal string without float arithmetic.

    Example:
        paise_to_paypal_amount_str(259900) -> "2599.00"
        paise_to_paypal_amount_str(99) -> "0.99"
    """
    if not isinstance(paise, int):
        raise TypeError(f"paise must be an integer, received {type(paise).__name__}")
    if paise < 0:
        raise ValueError("paise cannot be negative")
    dec = paise_to_decimal(paise)
    return f"{dec:.2f}"


def compute_landed_cost_paise(
    product_price_paise: int,
    shipping_cost_paise: Optional[int]
) -> Optional[int]:
    """Calculate total landed cost in paise (product price + shipping).

    If shipping_cost_paise is None (unknown), returns None to indicate
    unconfirmed total cost, preventing unknown shipping from being treated as free.
    Enforces non-negative integer arithmetic.
    """
    if product_price_paise < 0:
        raise ValueError("product_price_paise cannot be negative")
    if shipping_cost_paise is None:
        return None
    if shipping_cost_paise < 0:
        raise ValueError("shipping_cost_paise cannot be negative")
    return product_price_paise + shipping_cost_paise
