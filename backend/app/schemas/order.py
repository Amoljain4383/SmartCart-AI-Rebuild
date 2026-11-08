"""Pydantic schemas for Orders, Order Items, and PayPal Sandbox Checkout."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.core.currency import paise_to_rupees_str


class OrderItemCreate(BaseModel):
    """Client request item specification."""
    offer_id: str = Field(..., description="ID of the selected retailer offer")
    quantity: int = Field(1, ge=1, le=100, description="Quantity to purchase (1-100)")


class OrderCreateRequest(BaseModel):
    """Authenticated request to create an order."""
    items: List[OrderItemCreate] = Field(..., min_length=1, description="List of items to order")
    shipping_address: Optional[Dict[str, Any]] = Field(None, description="Optional shipping address dict")
    idempotency_key: Optional[str] = Field(None, description="Optional client idempotency key")


class OrderItemResponse(BaseModel):
    """Safe public representation of an item in an order."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    offer_id: str
    product_title_snapshot: Optional[str] = None
    retailer_name_snapshot: Optional[str] = None
    quantity: int
    unit_price_paise: int
    unit_price_formatted: str
    shipping_price_paise: int
    shipping_price_formatted: str
    total_item_paise: int
    total_item_formatted: str


class OrderResponse(BaseModel):
    """Full order details representation."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    status: str  # pending, paypal_created, paid, failed, cancelled
    total_paise: int
    total_formatted: str
    currency: str
    paypal_amount_str: Optional[str] = None
    paypal_currency: Optional[str] = None
    paypal_order_id: Optional[str] = None
    paypal_capture_id: Optional[str] = None
    simulated_order_notice: str
    items: List[OrderItemResponse] = []
    created_at: datetime
    updated_at: datetime


class PayPalOrderCreateResponse(BaseModel):
    """Safe response returned to client after server-side PayPal order creation."""
    order_id: str
    paypal_order_id: str
    status: str
    amount: str
    currency: str
    notice: str = "SmartCart simulated demo purchase. No actual retailer order placed."


class PayPalCaptureResponse(BaseModel):
    """Response returned upon successful server-verified payment capture."""
    order_id: str
    paypal_order_id: str
    paypal_capture_id: str
    status: str
    captured_amount: str
    captured_currency: str
    order: OrderResponse
    message: str = "Simulated PayPal transaction successfully captured and verified."
