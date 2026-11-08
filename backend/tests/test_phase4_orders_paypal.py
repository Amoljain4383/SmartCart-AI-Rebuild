"""Comprehensive automated tests for Phase 4: Orders & PayPal Sandbox Checkout."""
import json
import pytest
from app.core.config import settings
from app.core.security import hash_password, create_access_token
from app.models.user import User
from app.models.product import Product, RetailerOffer
from app.models.order import Order, OrderItem
from app.core.currency import paise_to_paypal_amount_str
from app.services.paypal_service import (
    paypal_service,
    PayPalConfigurationError,
    PayPalTimeoutError,
    PayPalApiError,
)


@pytest.fixture
def order_fixture(db_session):
    """Seed sample users, products, and offers for order testing."""
    user1 = User(
        email="buyer1@test.com",
        hashed_password=hash_password("Pass1234!"),
        full_name="Buyer One",
        role="user",
        is_active=True
    )
    user2 = User(
        email="buyer2@test.com",
        hashed_password=hash_password("Pass1234!"),
        full_name="Buyer Two",
        role="user",
        is_active=True
    )
    prod = Product(
        title="Test Noise Cancelling Headphones",
        category="Audio",
        brand="AudioBrand",
        is_active=True,
        is_demo_data=True
    )
    db_session.add_all([user1, user2, prod])
    db_session.flush()

    # Valid Offer: Price ₹25,999.00 (2599900 paise) + Shipping ₹499.00 (49900 paise)
    valid_offer = RetailerOffer(
        product_id=prod.id,
        retailer_name="SonicSound Store",
        product_price_paise=2599900,
        shipping_cost_paise=49900,
        is_shipping_known=True,
        total_cost_paise=2649800,
        is_active=True,
        is_demo_data=True
    )
    # Unknown shipping offer
    unknown_shipping_offer = RetailerOffer(
        product_id=prod.id,
        retailer_name="Unknown Store",
        product_price_paise=2000000,
        shipping_cost_paise=None,
        is_shipping_known=False,
        total_cost_paise=None,
        is_active=True,
        is_demo_data=True
    )
    # Inactive offer
    inactive_offer = RetailerOffer(
        product_id=prod.id,
        retailer_name="Inactive Store",
        product_price_paise=2200000,
        shipping_cost_paise=10000,
        is_shipping_known=True,
        total_cost_paise=2210000,
        is_active=False,
        is_demo_data=True
    )

    db_session.add_all([valid_offer, unknown_shipping_offer, inactive_offer])
    db_session.commit()

    return {
        "user1": user1,
        "user2": user2,
        "token1": create_access_token(subject=user1.id, role="user"),
        "token2": create_access_token(subject=user2.id, role="user"),
        "valid_offer": valid_offer,
        "unknown_shipping_offer": unknown_shipping_offer,
        "inactive_offer": inactive_offer,
    }


# =============================================================================
# 1. Order Creation & Recalculation Tests
# =============================================================================

def test_authenticated_order_creation_and_recalculation(api_client, order_fixture):
    """1, 4, 5: Authenticated order creation recalculates total on backend and ignores client amounts."""
    token = order_fixture["token1"]
    offer = order_fixture["valid_offer"]

    # Client submits spoofed price of ₹1.00 (100 paise) and total of ₹1.00
    exploit_payload = {
        "items": [
            {"offer_id": offer.id, "quantity": 2, "unit_price": 100, "total": 100}
        ],
        "shipping_address": {"city": "Bengaluru", "country": "IN"},
        "idempotency_key": "test-idem-001"
    }

    response = api_client.post(
        "/api/orders",
        json=exploit_payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    data = response.json()

    # Backend recalculated: (2599900 * 2) + 49900 = 5199800 + 49900 = 5249700 paise
    assert data["total_paise"] == 5249700
    assert data["total_formatted"] == "₹52,497.00"
    assert data["status"] == "pending"
    assert len(data["items"]) == 1
    assert data["items"][0]["unit_price_paise"] == 2599900
    assert data["items"][0]["shipping_price_paise"] == 49900


def test_unauthenticated_order_creation_rejected(api_client, order_fixture):
    """2. Unauthenticated order creation receives 401."""
    offer = order_fixture["valid_offer"]
    payload = {"items": [{"offer_id": offer.id, "quantity": 1}]}
    response = api_client.post("/api/orders", json=payload)
    assert response.status_code == 401


def test_users_cannot_view_other_users_orders(api_client, order_fixture, db_session):
    """3. User cannot access another user's order."""
    user1 = order_fixture["user1"]
    token2 = order_fixture["token2"]

    # Create order owned by user 1
    order1 = Order(
        user_id=user1.id,
        status="pending",
        total_paise=100000,
        currency="INR"
    )
    db_session.add(order1)
    db_session.commit()

    # User 2 tries to access User 1's order
    response = api_client.get(
        f"/api/orders/{order1.id}",
        headers={"Authorization": f"Bearer {token2}"}
    )
    assert response.status_code == 404
    assert "order not found" in response.json()["detail"].lower()


def test_unknown_shipping_prevents_checkout(api_client, order_fixture):
    """6. Unknown shipping prevents order creation."""
    token = order_fixture["token1"]
    unknown_offer = order_fixture["unknown_shipping_offer"]

    response = api_client.post(
        "/api/orders",
        json={"items": [{"offer_id": unknown_offer.id, "quantity": 1}]},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert "unknown shipping" in response.json()["detail"].lower()


def test_inactive_offer_prevents_checkout(api_client, order_fixture):
    """7. Inactive offer prevents order creation."""
    token = order_fixture["token1"]
    inactive_offer = order_fixture["inactive_offer"]

    response = api_client.post(
        "/api/orders",
        json={"items": [{"offer_id": inactive_offer.id, "quantity": 1}]},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert "inactive" in response.json()["detail"].lower()


# =============================================================================
# 2. Currency & PayPal Amount Formatting Tests
# =============================================================================

def test_paise_to_paypal_amount_formatting():
    """8. Correct paise to PayPal 2-decimal amount string without float errors."""
    assert paise_to_paypal_amount_str(259900) == "2599.00"
    assert paise_to_paypal_amount_str(10) == "0.10"
    assert paise_to_paypal_amount_str(99) == "0.99"
    assert paise_to_paypal_amount_str(12345678) == "123456.78"
    assert paise_to_paypal_amount_str(0) == "0.00"

    with pytest.raises(ValueError):
        paise_to_paypal_amount_str(-100)


def test_currency_mismatch_rejected(api_client, order_fixture, monkeypatch):
    """9. Currency mismatch between order and PayPal rejects checkout."""
    token = order_fixture["token1"]
    offer = order_fixture["valid_offer"]

    # Create order in INR
    order_resp = api_client.post(
        "/api/orders",
        json={"items": [{"offer_id": offer.id, "quantity": 1}]},
        headers={"Authorization": f"Bearer {token}"}
    )
    order_id = order_resp.json()["id"]

    # Simulate PayPal configured for USD while order is INR
    monkeypatch.setattr(settings, "PAYPAL_CURRENCY", "USD")

    resp = api_client.post(
        f"/api/orders/{order_id}/paypal/create",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 400
    assert "currency mismatch" in resp.json()["detail"].lower()


# =============================================================================
# 3. PayPal Order Creation & Capture Mocked Tests
# =============================================================================

def test_paypal_order_creation_mocked(api_client, order_fixture, monkeypatch):
    """10. PayPal order creation using mocked Sandbox response."""
    token = order_fixture["token1"]
    offer = order_fixture["valid_offer"]

    order_resp = api_client.post(
        "/api/orders",
        json={"items": [{"offer_id": offer.id, "quantity": 1}]},
        headers={"Authorization": f"Bearer {token}"}
    )
    order_id = order_resp.json()["id"]

    # Mock PayPal service create call
    def mock_create(amount_str, currency, reference_id, idempotency_key=None):
        assert amount_str == "26498.00"
        assert currency == "INR"
        return {"id": "MOCK_PAYPAL_ORDER_12345", "status": "CREATED"}

    monkeypatch.setattr(paypal_service, "create_paypal_order", mock_create)

    response = api_client.post(
        f"/api/orders/{order_id}/paypal/create",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["paypal_order_id"] == "MOCK_PAYPAL_ORDER_12345"
    assert data["status"] == "paypal_created"
    assert data["amount"] == "26498.00"
    assert data["currency"] == "INR"


def test_missing_paypal_credentials_handled_safely(api_client, order_fixture, monkeypatch):
    """11. Missing or placeholder credentials raise HTTP 503 safely."""
    token = order_fixture["token1"]
    offer = order_fixture["valid_offer"]

    order_resp = api_client.post(
        "/api/orders",
        json={"items": [{"offer_id": offer.id, "quantity": 1}]},
        headers={"Authorization": f"Bearer {token}"}
    )
    order_id = order_resp.json()["id"]

    def mock_fail(*args, **kwargs):
        raise PayPalConfigurationError("PayPal Sandbox credentials are not configured on the server.")

    monkeypatch.setattr(paypal_service, "create_paypal_order", mock_fail)

    response = api_client.post(
        f"/api/orders/{order_id}/paypal/create",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"].lower()


def test_successful_capture_mocked(api_client, order_fixture, db_session, monkeypatch):
    """12. Successful payment capture transitions order to 'paid'."""
    user1 = order_fixture["user1"]
    token = order_fixture["token1"]

    order = Order(
        user_id=user1.id,
        status="paypal_created",
        total_paise=2649800,  # ₹26,498.00 -> "26498.00"
        currency="INR",
        paypal_order_id="MOCK_PP_ORDER_SUCCESS",
        paypal_amount_str="26498.00",
        paypal_currency="INR"
    )
    db_session.add(order)
    db_session.commit()

    # Mock PayPal capture response
    mock_capture_payload = {
        "status": "COMPLETED",
        "purchase_units": [
            {
                "payments": {
                    "captures": [
                        {
                            "id": "MOCK_CAPTURE_ID_987",
                            "status": "COMPLETED",
                            "amount": {
                                "value": "26498.00",
                                "currency_code": "INR"
                            }
                        }
                    ]
                }
            }
        ]
    }
    monkeypatch.setattr(paypal_service, "capture_paypal_order", lambda *args, **kwargs: mock_capture_payload)

    response = api_client.post(
        f"/api/orders/{order.id}/paypal/capture",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "paid"
    assert data["paypal_capture_id"] == "MOCK_CAPTURE_ID_987"
    assert data["order"]["status"] == "paid"


def test_incorrect_captured_amount_rejected(api_client, order_fixture, db_session, monkeypatch):
    """13. Captured amount mismatch sets order to 'failed' and rejects with 400."""
    user1 = order_fixture["user1"]
    token = order_fixture["token1"]

    order = Order(
        user_id=user1.id,
        status="paypal_created",
        total_paise=2649800,  # Expected: "26498.00"
        currency="INR",
        paypal_order_id="MOCK_PP_WRONG_AMOUNT",
        paypal_amount_str="26498.00",
        paypal_currency="INR"
    )
    db_session.add(order)
    db_session.commit()

    # PayPal returns different captured amount
    mock_bad_amount = {
        "status": "COMPLETED",
        "purchase_units": [
            {
                "payments": {
                    "captures": [
                        {
                            "id": "CAP_WRONG",
                            "status": "COMPLETED",
                            "amount": {"value": "100.00", "currency_code": "INR"}  # Fraudulent mismatch!
                        }
                    ]
                }
            }
        ]
    }
    monkeypatch.setattr(paypal_service, "capture_paypal_order", lambda *args, **kwargs: mock_bad_amount)

    response = api_client.post(
        f"/api/orders/{order.id}/paypal/capture",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert "amount mismatch" in response.json()["detail"].lower()

    # Verify order status was set to failed in DB
    db_session.refresh(order)
    assert order.status == "failed"


def test_incorrect_currency_rejected(api_client, order_fixture, db_session, monkeypatch):
    """14. Captured currency mismatch sets order to 'failed' and rejects with 400."""
    user1 = order_fixture["user1"]
    token = order_fixture["token1"]

    order = Order(
        user_id=user1.id,
        status="paypal_created",
        total_paise=2649800,
        currency="INR",
        paypal_order_id="MOCK_PP_WRONG_CURR",
        paypal_amount_str="26498.00",
        paypal_currency="INR"
    )
    db_session.add(order)
    db_session.commit()

    mock_bad_currency = {
        "status": "COMPLETED",
        "purchase_units": [
            {
                "payments": {
                    "captures": [
                        {
                            "id": "CAP_CURR",
                            "status": "COMPLETED",
                            "amount": {"value": "26498.00", "currency_code": "USD"}  # Currency mismatch!
                        }
                    ]
                }
            }
        ]
    }
    monkeypatch.setattr(paypal_service, "capture_paypal_order", lambda *args, **kwargs: mock_bad_currency)

    response = api_client.post(
        f"/api/orders/{order.id}/paypal/capture",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert "currency mismatch" in response.json()["detail"].lower()
    db_session.refresh(order)
    assert order.status == "failed"


def test_duplicate_capture_protection(api_client, order_fixture, db_session, monkeypatch):
    """15. Repeated capture requests on an already paid order are safely handled without duplicate captures."""
    user1 = order_fixture["user1"]
    token = order_fixture["token1"]

    order = Order(
        user_id=user1.id,
        status="paid",  # Already captured
        total_paise=2649800,
        currency="INR",
        paypal_order_id="MOCK_PP_ALREADY_PAID",
        paypal_capture_id="EXISTING_CAPTURE_123",
        paypal_amount_str="26498.00",
        paypal_currency="INR"
    )
    db_session.add(order)
    db_session.commit()

    # Capture called again
    capture_mock_called = False
    def mock_capture(*args, **kwargs):
        nonlocal capture_mock_called
        capture_mock_called = True
        return {}

    monkeypatch.setattr(paypal_service, "capture_paypal_order", mock_capture)

    response = api_client.post(
        f"/api/orders/{order.id}/paypal/capture",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "paid"
    assert "already captured" in response.json()["message"].lower()
    # Confirm PayPal capture API was NOT called again
    assert capture_mock_called is False


def test_paypal_timeout_handling(api_client, order_fixture, db_session, monkeypatch):
    """16. PayPal timeout does not mark order as paid."""
    user1 = order_fixture["user1"]
    token = order_fixture["token1"]

    order = Order(
        user_id=user1.id,
        status="paypal_created",
        total_paise=2649800,
        currency="INR",
        paypal_order_id="MOCK_PP_TIMEOUT",
        paypal_amount_str="26498.00",
        paypal_currency="INR"
    )
    db_session.add(order)
    db_session.commit()

    def mock_timeout(*args, **kwargs):
        raise PayPalTimeoutError("Connection timed out.")

    monkeypatch.setattr(paypal_service, "capture_paypal_order", mock_timeout)

    response = api_client.post(
        f"/api/orders/{order.id}/paypal/capture",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 504
    assert "timed out" in response.json()["detail"].lower()

    # Verify order is NOT paid
    db_session.refresh(order)
    assert order.status == "paypal_created"


def test_invalid_order_state_transitions(api_client, order_fixture, db_session):
    """17. Invalid order state transitions are rejected."""
    user1 = order_fixture["user1"]
    token = order_fixture["token1"]

    # Cancelled order
    cancelled_order = Order(
        user_id=user1.id,
        status="cancelled",
        total_paise=100000,
        currency="INR"
    )
    db_session.add(cancelled_order)
    db_session.commit()

    # Attempt create on cancelled order
    r_create = api_client.post(
        f"/api/orders/{cancelled_order.id}/paypal/create",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert r_create.status_code == 400

    # Attempt capture on cancelled order
    r_cap = api_client.post(
        f"/api/orders/{cancelled_order.id}/paypal/capture",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert r_cap.status_code == 400
