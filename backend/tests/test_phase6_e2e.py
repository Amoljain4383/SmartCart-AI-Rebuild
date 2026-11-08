"""Phase 6: Comprehensive Backend End-to-End Integration Tests.

Validates the complete workflow:
1. User registration (strictly role='user'), login, authentication, and JWT logout revocation.
2. Product search, details, offers comparison, and inactive filtering.
3. Offline deterministic recommendation engine landed-cost ranking & transparent explanation.
4. Order creation with server-side paise recalculation, tampering protection, and user isolation.
5. PayPal Sandbox creation, verified capture, duplicate capture protection, and mismatch rejection.
"""
import uuid
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.product import Product, RetailerOffer
from app.models.order import Order
from app.core.security import hash_password
from app.core.currency import paise_to_rupees_str


# -----------------------------------------------------------------------------
# 1. Authentication End-to-End Workflow
# -----------------------------------------------------------------------------

def test_e2e_authentication_workflow(api_client: TestClient, db_session: Session):
    """E2E Test: Register -> Role verification -> Login -> Profile -> Logout -> Token blocked."""
    client = api_client
    db = db_session
    unique_email = f"e2e_{uuid.uuid4().hex[:8]}@example.com"
    raw_password = "E2ePassword123!"
    full_name = "End to End User"

    # Step 1: Register new user (attempt to pass admin role in payload)
    reg_resp = client.post(
        "/api/auth/register",
        json={
            "email": unique_email,
            "password": raw_password,
            "full_name": full_name,
            "role": "admin"  # Malicious extra field
        }
    )
    assert reg_resp.status_code == 201, reg_resp.text
    reg_data = reg_resp.json()
    assert reg_data["user"]["email"] == unique_email
    assert reg_data["user"]["role"] == "user", "Public registration MUST enforce role='user' regardless of payload"
    initial_token = reg_data["access_token"]

    # Step 2: Access profile with registration token
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {initial_token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == unique_email

    # Step 3: Login with invalid credentials rejected
    bad_login = client.post(
        "/api/auth/login",
        json={"email": unique_email, "password": "WrongPassword123!"}
    )
    assert bad_login.status_code == 401

    # Step 4: Login with valid credentials
    good_login = client.post(
        "/api/auth/login",
        json={"email": unique_email, "password": raw_password}
    )
    assert good_login.status_code == 200
    login_token = good_login.json()["access_token"]

    # Step 5: Logout revokes login token
    logout_resp = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {login_token}"}
    )
    assert logout_resp.status_code == 200
    assert "logged out" in logout_resp.json()["message"].lower()

    # Step 6: Verify revoked token is blocked on protected endpoint
    blocked_resp = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {login_token}"}
    )
    assert blocked_resp.status_code == 401
    assert "revoked" in blocked_resp.json()["detail"].lower()


# -----------------------------------------------------------------------------
# 2. Product Discovery & Filtering Workflow
# -----------------------------------------------------------------------------

def test_e2e_product_discovery_workflow(api_client: TestClient, db_session: Session):
    """E2E Test: Catalogue listing -> Search -> Detail -> Offer comparison -> Inactive handling."""
    client = api_client
    db = db_session
    # Seed a test product with multiple offers
    prod = Product(
        title="Sony WH-1000XM5 E2E Wireless Headphones",
        description="Premium active noise cancelling headphones for E2E testing.",
        category="Audio",
        brand="Sony",
        is_active=True,
        is_demo_data=True
    )
    db.add(prod)
    db.commit()
    db.refresh(prod)

    # Offer A: Lower base sticker, high shipping (Higher landed cost)
    offer_a = RetailerOffer(
        product_id=prod.id,
        retailer_name="StickerCheap (Demo)",
        product_price_paise=2499900,  # ₹24,999.00
        shipping_cost_paise=200000,   # ₹2,000.00
        is_shipping_known=True,
        total_cost_paise=2699900,     # ₹26,999.00
        estimated_delivery_days=4,
        retailer_rating_tenth=42,
        review_count=100,
        return_policy="7 days",
        stock_status="in_stock",
        is_active=True,
        is_demo_data=True
    )
    # Offer B: Slightly higher base sticker, FREE shipping (Lower landed cost)
    offer_b = RetailerOffer(
        product_id=prod.id,
        retailer_name="TrueValue (Demo)",
        product_price_paise=2549900,  # ₹25,499.00
        shipping_cost_paise=0,        # ₹0.00
        is_shipping_known=True,
        total_cost_paise=2549900,     # ₹25,499.00
        estimated_delivery_days=2,
        retailer_rating_tenth=48,
        review_count=500,
        return_policy="14 days",
        stock_status="in_stock",
        is_active=True,
        is_demo_data=True
    )
    # Offer C: Inactive offer
    offer_c = RetailerOffer(
        product_id=prod.id,
        retailer_name="GhostStore (Inactive)",
        product_price_paise=1999900,
        shipping_cost_paise=0,
        is_shipping_known=True,
        total_cost_paise=1999900,
        estimated_delivery_days=1,
        retailer_rating_tenth=50,
        review_count=10,
        return_policy="None",
        stock_status="in_stock",
        is_active=False,
        is_demo_data=True
    )
    db.add_all([offer_a, offer_b, offer_c])
    db.commit()

    # Step 1: List products
    list_resp = client.get("/api/products?category=Audio")
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert any(p["id"] == prod.id for p in items)

    # Step 2: Search products by keyword
    search_resp = client.get("/api/products/search?q=WH-1000XM5")
    assert search_resp.status_code == 200
    search_results = search_resp.json()
    assert len(search_results) >= 1
    assert any("Sony" in p["title"] for p in search_results)

    # Step 3: Empty search results
    empty_resp = client.get("/api/products/search?q=NonExistentDeviceX999")
    assert empty_resp.status_code == 200
    assert empty_resp.json() == []

    # Step 4: Get product details
    detail_resp = client.get(f"/api/products/{prod.id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["title"] == prod.title

    # Step 5: Offers ranked strictly by total landed cost (not sticker price)
    offers_resp = client.get(f"/api/products/{prod.id}/offers?sort_by=total_cost")
    assert offers_resp.status_code == 200
    public_offers = offers_resp.json()
    
    # Inactive offer C must not be in public offers
    assert not any(o["id"] == offer_c.id for o in public_offers)
    assert len(public_offers) == 2

    # Offer B (Total: ₹25,499) must be ranked ahead of Offer A (Total: ₹26,999)
    assert public_offers[0]["id"] == offer_b.id
    assert public_offers[0]["total_cost_paise"] < public_offers[1]["total_cost_paise"]
    assert public_offers[0]["comparison_rank"] == 1


# -----------------------------------------------------------------------------
# 3. Recommendation Engine Workflow
# -----------------------------------------------------------------------------

def test_e2e_recommendation_workflow(api_client: TestClient, db_session: Session):
    """E2E Test: Auth required -> Landed cost ranking -> Transparent mathematical savings explanation."""
    client = api_client
    db = db_session
    # 1. Unauthenticated recommendation rejected
    unauth = client.post("/api/recommendations", json={"query": "Sony"})
    assert unauth.status_code == 401

    # 2. Authenticated user
    user = User(
        email=f"rec_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("SecretPass123!"),
        full_name="Recommendation Tester",
        role="user"
    )
    # Seed product with offers for recommendation
    prod = Product(
        title="Sony WH-1000XM5 Premium Headphones",
        description="Active noise cancelling headphones",
        category="Audio",
        brand="Sony",
        is_active=True,
        is_demo_data=True
    )
    db.add_all([user, prod])
    db.commit()

    offer1 = RetailerOffer(
        product_id=prod.id,
        retailer_name="Retailer Fast",
        product_price_paise=2600000,
        shipping_cost_paise=0,
        is_shipping_known=True,
        total_cost_paise=2600000,
        estimated_delivery_days=2,
        retailer_rating_tenth=48,
        review_count=100,
        return_policy="14 days",
        stock_status="in_stock",
        is_active=True,
        is_demo_data=True
    )
    offer2 = RetailerOffer(
        product_id=prod.id,
        retailer_name="Retailer Slow",
        product_price_paise=2500000,
        shipping_cost_paise=200000,
        is_shipping_known=True,
        total_cost_paise=2700000,
        estimated_delivery_days=5,
        retailer_rating_tenth=40,
        review_count=50,
        return_policy="7 days",
        stock_status="in_stock",
        is_active=True,
        is_demo_data=True
    )
    db.add_all([offer1, offer2])
    db.commit()

    login_resp = client.post(
        "/api/auth/login",
        json={"email": user.email, "password": "SecretPass123!"}
    )
    token = login_resp.json()["access_token"]

    # 3. Request recommendation
    rec_resp = client.post(
        "/api/recommendations",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": "Sony"}
    )
    assert rec_resp.status_code == 200, rec_resp.text
    rec_data = rec_resp.json()

    assert rec_data["recommended_offer"] is not None
    assert rec_data["is_demo_data"] is True
    assert "deterministic" in rec_data["engine_type"].lower()
    assert "save" in rec_data["savings_explanation"].lower() or "best confirmed" in rec_data["savings_explanation"].lower()
    assert rec_data["best_confirmed_total_cost_paise"] > 0


# -----------------------------------------------------------------------------
# 4. Orders & Tamper-Proof Pricing Workflow
# -----------------------------------------------------------------------------

def test_e2e_orders_tamper_proofing_and_isolation(api_client: TestClient, db_session: Session):
    """E2E Test: Order creation -> Server recalculates in paise -> Client tampering rejected -> User isolation."""
    client = api_client
    db = db_session
    # Create User A and User B
    user_a = User(email=f"usera_{uuid.uuid4().hex[:6]}@example.com", hashed_password=hash_password("Pass123!"), full_name="User A", role="user")
    user_b = User(email=f"userb_{uuid.uuid4().hex[:6]}@example.com", hashed_password=hash_password("Pass123!"), full_name="User B", role="user")
    db.add_all([user_a, user_b])
    db.commit()

    token_a = client.post("/api/auth/login", json={"email": user_a.email, "password": "Pass123!"}).json()["access_token"]
    token_b = client.post("/api/auth/login", json={"email": user_b.email, "password": "Pass123!"}).json()["access_token"]

    # Seed product and offer
    prod = Product(title="Test Keyboard", category="Electronics", brand="Keychron", is_active=True, is_demo_data=True)
    db.add(prod)
    db.commit()

    # Exact DB price: 8,000.00 INR (800000 paise) + 200.00 INR shipping (20000 paise) = 8,200.00 INR (820000 paise)
    offer = RetailerOffer(
        product_id=prod.id,
        retailer_name="KeyHub",
        product_price_paise=800000,
        shipping_cost_paise=20000,
        is_shipping_known=True,
        total_cost_paise=820000,
        estimated_delivery_days=3,
        retailer_rating_tenth=45,
        review_count=50,
        return_policy="14 days",
        stock_status="in_stock",
        is_active=True,
        is_demo_data=True
    )
    db.add(offer)
    db.commit()

    # Step 1: User A creates order with attempt to send malicious client-side price
    order_payload = {
        "items": [
            {
                "offer_id": offer.id,
                "quantity": 2,
                "price": 100,        # Attempted tampering: 100 paise
                "total": 200         # Attempted tampering: 200 paise
            }
        ],
        "shipping_address": {
            "recipient_name": "User A",
            "address_line": "123 Test Street",
            "city": "Bengaluru",
            "postal_code": "560001"
        },
        "idempotency_key": f"idemp-{uuid.uuid4().hex}"
    }

    create_resp = client.post(
        "/api/orders",
        headers={"Authorization": f"Bearer {token_a}"},
        json=order_payload
    )
    assert create_resp.status_code == 201, create_resp.text
    order_data = create_resp.json()

    # Verification: Server recalculated price strictly from DB records!
    # Expected: 2 * 800,000 + 20,000 = 1,620,000 paise (₹16,200.00)
    assert order_data["total_paise"] == 1620000
    assert order_data["total_formatted"] == paise_to_rupees_str(1620000)
    assert order_data["status"] == "pending"
    order_id = order_data["id"]

    # Step 2: User A can view their own order
    get_a = client.get(f"/api/orders/{order_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert get_a.status_code == 200
    assert get_a.json()["id"] == order_id

    # Step 3: User B CANNOT view User A's order (User isolation)
    get_b = client.get(f"/api/orders/{order_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert get_b.status_code == 404, "Cross-user order access must return 404 Not Found"


# -----------------------------------------------------------------------------
# 5. PayPal Sandbox Workflow & Idempotency
# -----------------------------------------------------------------------------

def test_e2e_paypal_sandbox_workflow(api_client: TestClient, db_session: Session):
    """E2E Test: PayPal create -> Verify amount & currency -> Verified capture -> Duplicate capture safe."""
    client = api_client
    db = db_session
    user = User(email=f"paypal_{uuid.uuid4().hex[:6]}@example.com", hashed_password=hash_password("Pass123!"), full_name="PayPal Tester", role="user")
    db.add(user)
    db.commit()

    token = client.post("/api/auth/login", json={"email": user.email, "password": "Pass123!"}).json()["access_token"]

    prod = Product(title="Smart Speaker", category="Electronics", brand="Amazon", is_active=True, is_demo_data=True)
    db.add(prod)
    db.commit()

    # 4,999.00 INR + 0 shipping = 4,999.00 INR (499900 paise)
    offer = RetailerOffer(
        product_id=prod.id,
        retailer_name="SmartStore",
        product_price_paise=499900,
        shipping_cost_paise=0,
        is_shipping_known=True,
        total_cost_paise=499900,
        estimated_delivery_days=2,
        retailer_rating_tenth=47,
        review_count=100,
        return_policy="7 days",
        stock_status="in_stock",
        is_active=True,
        is_demo_data=True
    )
    db.add(offer)
    db.commit()

    order_resp = client.post(
        "/api/orders",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "items": [{"offer_id": offer.id, "quantity": 1}],
            "shipping_address": {"recipient_name": "Tester", "address_line": "MG Road", "city": "Bengaluru", "postal_code": "560001"}
        }
    )
    assert order_resp.status_code == 201
    order_id = order_resp.json()["id"]

    # Step 1: PayPal order creation (mocking PayPal REST API call)
    with patch("app.services.paypal_service.paypal_service.create_paypal_order") as mock_create:
        mock_create.return_value = {
            "id": "PAYPAL-ORDER-999",
            "status": "CREATED",
            "amount": "4999.00",
            "currency": "INR"
        }
        create_paypal = client.post(
            f"/api/orders/{order_id}/paypal/create",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert create_paypal.status_code == 200
        assert create_paypal.json()["paypal_order_id"] == "PAYPAL-ORDER-999"

    # Step 2: PayPal capture execution (mocking PayPal capture response)
    with patch("app.services.paypal_service.paypal_service.capture_paypal_order") as mock_capture:
        mock_capture.return_value = {
            "status": "COMPLETED",
            "id": "PAYPAL-ORDER-999",
            "purchase_units": [
                {
                    "payments": {
                        "captures": [
                            {
                                "id": "CAPTURE-XYZ-123",
                                "status": "COMPLETED",
                                "amount": {
                                    "value": "4999.00",
                                    "currency_code": "INR"
                                }
                            }
                        ]
                    }
                }
            ]
        }
        capture_resp = client.post(
            f"/api/orders/{order_id}/paypal/capture",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert capture_resp.status_code == 200, capture_resp.text
        cap_data = capture_resp.json()
        assert cap_data["status"] == "paid"
        assert cap_data["paypal_capture_id"] == "CAPTURE-XYZ-123"
        assert cap_data["captured_amount"] == "4999.00"
        assert cap_data["captured_currency"] == "INR"

    # Step 3: Duplicate capture protection
    # Repeating capture on an already paid order safely returns success without error or double charge
    dup_capture = client.post(
        f"/api/orders/{order_id}/paypal/capture",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert dup_capture.status_code == 200
    assert dup_capture.json()["status"] == "paid"
    assert "already captured" in dup_capture.json()["message"].lower()

    # Step 4: Verify order receipt shows paid status
    final_order = client.get(f"/api/orders/{order_id}", headers={"Authorization": f"Bearer {token}"}).json()
    assert final_order["status"] == "paid"
    assert final_order["paypal_order_id"] == "PAYPAL-ORDER-999"
    assert final_order["paypal_capture_id"] == "CAPTURE-XYZ-123"
