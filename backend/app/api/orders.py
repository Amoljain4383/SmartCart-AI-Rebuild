"""Orders API Router: Authenticated Order Creation, History, and PayPal Sandbox Checkout."""
import json
import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.api.deps import get_current_user
from app.models.user import User
from app.models.product import RetailerOffer
from app.models.order import Order, OrderItem
from app.models.base import utc_now
from app.schemas.order import (
    OrderCreateRequest,
    OrderResponse,
    OrderItemResponse,
    PayPalOrderCreateResponse,
    PayPalCaptureResponse,
)
from app.core.currency import (
    paise_to_paypal_amount_str,
    paise_to_rupees_str,
    compute_landed_cost_paise,
)
from app.services.paypal_service import (
    paypal_service,
    PayPalService,
    PayPalConfigurationError,
    PayPalApiError,
    PayPalTimeoutError,
)

router = APIRouter(prefix="", tags=["Orders & Payments"])


def _format_order_response(order: Order) -> OrderResponse:
    """Helper to convert Order ORM into OrderResponse with items."""
    item_responses = [
        OrderItemResponse(
            id=item.id,
            offer_id=item.offer_id,
            product_title_snapshot=item.product_title_snapshot,
            retailer_name_snapshot=item.retailer_name_snapshot,
            quantity=item.quantity,
            unit_price_paise=item.unit_price_paise,
            unit_price_formatted=paise_to_rupees_str(item.unit_price_paise),
            shipping_price_paise=item.shipping_price_paise,
            shipping_price_formatted=paise_to_rupees_str(item.shipping_price_paise),
            total_item_paise=item.total_item_paise,
            total_item_formatted=paise_to_rupees_str(item.total_item_paise),
        )
        for item in order.items
    ]

    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        status=order.status.lower(),
        total_paise=order.total_paise,
        total_formatted=paise_to_rupees_str(order.total_paise),
        currency=order.currency,
        paypal_amount_str=order.paypal_amount_str,
        paypal_currency=order.paypal_currency,
        paypal_order_id=order.paypal_order_id,
        paypal_capture_id=order.paypal_capture_id,
        simulated_order_notice=order.simulated_order_notice,
        items=item_responses,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


# -----------------------------------------------------------------------------
# 1. Order Creation & History
# -----------------------------------------------------------------------------

@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an authenticated order with server-recalculated prices"
)
def create_order(
    request: OrderCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create an order from selected retailer offers.

    Security & Precision:
    - Never trusts client-submitted prices or totals.
    - Recalculates exact product and shipping charges in integer paise from database records.
    - Rejects inactive products, inactive offers, out of stock, and offers with unknown shipping.
    - Supports client idempotency keys to prevent duplicate order submissions.
    """
    # Check client idempotency key
    if request.idempotency_key:
        existing_order = db.query(Order).filter(
            Order.user_id == current_user.id,
            Order.idempotency_key == request.idempotency_key
        ).first()
        if existing_order:
            return _format_order_response(existing_order)

    total_order_paise = 0
    created_items: List[OrderItem] = []

    for item_spec in request.items:
        offer = db.query(RetailerOffer).filter(RetailerOffer.id == item_spec.offer_id).first()
        if not offer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Retailer offer '{item_spec.offer_id}' does not exist."
            )

        # Enforce active and valid status
        if not offer.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Offer from '{offer.retailer_name}' is currently inactive and cannot be ordered."
            )
        if not offer.product.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product '{offer.product.title}' is currently inactive."
            )
        if not offer.is_shipping_known or offer.shipping_cost_paise is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Offer from '{offer.retailer_name}' has unknown shipping charges. Total cost cannot be confirmed for checkout."
            )
        if offer.stock_status == "out_of_stock":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Offer from '{offer.retailer_name}' is out of stock."
            )

        # Recalculate strictly on backend using integer paise
        unit_price = offer.product_price_paise
        shipping_fee = offer.shipping_cost_paise
        item_total = (unit_price * item_spec.quantity) + shipping_fee

        total_order_paise += item_total

        order_item = OrderItem(
            offer_id=offer.id,
            product_title_snapshot=offer.product.title,
            retailer_name_snapshot=offer.retailer_name,
            quantity=item_spec.quantity,
            unit_price_paise=unit_price,
            shipping_price_paise=shipping_fee,
            total_item_paise=item_total
        )
        created_items.append(order_item)

    idempotency_key = request.idempotency_key or str(uuid.uuid4())

    new_order = Order(
        user_id=current_user.id,
        status="pending",
        total_paise=total_order_paise,
        currency=settings.CURRENCY,
        idempotency_key=idempotency_key,
        shipping_address_json=json.dumps(request.shipping_address) if request.shipping_address else None,
        simulated_order_notice="SmartCart simulated demo purchase. No actual retailer order placed."
    )
    new_order.items = created_items

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return _format_order_response(new_order)


@router.get(
    "",
    response_model=List[OrderResponse],
    summary="List authenticated user's order history"
)
def get_my_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all orders placed by the authenticated user."""
    orders = (
        db.query(Order)
        .filter(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return [_format_order_response(o) for o in orders]


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Retrieve order receipt details"
)
def get_order_by_id(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve single order details.

    Users can only access their own orders. Admins can view any order.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    if order.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    return _format_order_response(order)


# -----------------------------------------------------------------------------
# 2. PayPal Sandbox Checkout
# -----------------------------------------------------------------------------

@router.post(
    "/{order_id}/paypal/create",
    response_model=PayPalOrderCreateResponse,
    summary="Create PayPal Sandbox order for payment capture"
)
def create_paypal_order_endpoint(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Initiate PayPal Sandbox order on the server.

    Requirements:
    - Never exposes PayPal client secret to frontend.
    - Enforces currency matching.
    - Does not mark order as paid upon creation.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order or (order.user_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    norm_status = order.status.lower()
    if norm_status == "paid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order has already been paid and captured."
        )
    if norm_status in ("cancelled", "failed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot initiate payment for an order with status '{order.status}'."
        )

    # Currency validation: ensure order currency matches configured PayPal currency
    if order.currency.upper() != settings.PAYPAL_CURRENCY.upper():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Currency mismatch: Order source currency '{order.currency}' does not match "
                f"configured PayPal currency '{settings.PAYPAL_CURRENCY}'. "
                f"Automated currency conversion is not enabled."
            )
        )

    amount_str = paise_to_paypal_amount_str(order.total_paise)

    # Communicate with PayPal Sandbox
    try:
        paypal_resp = paypal_service.create_paypal_order(
            amount_str=amount_str,
            currency=order.currency,
            reference_id=order.id,
            idempotency_key=order.idempotency_key
        )
    except PayPalConfigurationError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except PayPalTimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(e)
        )
    except PayPalApiError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"PayPal API error: {e}"
        )

    paypal_order_id = paypal_resp.get("id")
    if not paypal_order_id:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="PayPal response did not contain an order ID."
        )

    # Update order state
    order.paypal_order_id = paypal_order_id
    order.paypal_amount_str = amount_str
    order.paypal_currency = order.currency
    order.status = "paypal_created"
    order.updated_at = utc_now()
    db.commit()
    db.refresh(order)

    return PayPalOrderCreateResponse(
        order_id=order.id,
        paypal_order_id=paypal_order_id,
        status=order.status,
        amount=amount_str,
        currency=order.currency
    )


@router.post(
    "/{order_id}/paypal/capture",
    response_model=PayPalCaptureResponse,
    summary="Capture and verify PayPal Sandbox payment on backend"
)
def capture_paypal_order_endpoint(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Capture payment funds via PayPal Sandbox and verify amount/currency.

    Protections:
    - Verifies order ownership.
    - Prevents duplicate captures.
    - Verifies server-calculated amount and currency against PayPal's capture payload.
    - Atomic database state transition to 'paid'.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order or (order.user_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    norm_status = order.status.lower()

    # Duplicate-capture protection
    if norm_status == "paid":
        return PayPalCaptureResponse(
            order_id=order.id,
            paypal_order_id=order.paypal_order_id or "",
            paypal_capture_id=order.paypal_capture_id or "",
            status="paid",
            captured_amount=order.paypal_amount_str or paise_to_paypal_amount_str(order.total_paise),
            captured_currency=order.currency,
            order=_format_order_response(order),
            message="Order already captured and paid. Duplicate capture was safely ignored."
        )

    # State validation
    if norm_status not in ("pending", "paypal_created"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid order state transition: Cannot capture order in '{order.status}' status."
        )

    if not order.paypal_order_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PayPal order has not been initialized for this order yet."
        )

    # Capture through PayPal Sandbox
    try:
        capture_data = paypal_service.capture_paypal_order(
            paypal_order_id=order.paypal_order_id,
            idempotency_key=f"cap-{order.idempotency_key}"
        )
    except PayPalConfigurationError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except PayPalTimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Payment capture timed out. The order remains in '{order.status}'. Please retry: {e}"
        )
    except PayPalApiError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"PayPal Capture error: {e}")

    # Inspect PayPal capture payload
    capture_status = capture_data.get("status")
    if capture_status != "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment capture status is '{capture_status}', not 'COMPLETED'."
        )

    try:
        purchase_unit = capture_data["purchase_units"][0]
        capture_entry = purchase_unit["payments"]["captures"][0]
        captured_amount = capture_entry["amount"]["value"]
        captured_currency = capture_entry["amount"]["currency_code"]
        capture_id = capture_entry["id"]
    except (KeyError, IndexError) as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unexpected PayPal capture payload structure: missing key {e}"
        )

    expected_amount = paise_to_paypal_amount_str(order.total_paise)
    expected_currency = order.currency.upper()

    # Strict server verification
    if captured_amount != expected_amount:
        order.status = "failed"
        order.updated_at = utc_now()
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Captured amount mismatch! Expected {expected_amount}, received {captured_amount}."
        )

    if captured_currency.upper() != expected_currency:
        order.status = "failed"
        order.updated_at = utc_now()
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Captured currency mismatch! Expected {expected_currency}, received {captured_currency}."
        )

    # Atomic success transition
    order.status = "paid"
    order.paypal_capture_id = capture_id
    order.paypal_amount_str = captured_amount
    order.paypal_currency = captured_currency
    order.updated_at = utc_now()
    db.commit()
    db.refresh(order)

    return PayPalCaptureResponse(
        order_id=order.id,
        paypal_order_id=order.paypal_order_id,
        paypal_capture_id=capture_id,
        status="paid",
        captured_amount=captured_amount,
        captured_currency=captured_currency,
        order=_format_order_response(order),
        message="Simulated PayPal Sandbox purchase successfully captured and verified on the server."
    )
