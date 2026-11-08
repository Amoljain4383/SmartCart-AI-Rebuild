"""Comprehensive automated tests for Phase 3: Catalogue, Comparison & Recommendations."""
import pytest
from app.core.security import hash_password, create_access_token
from app.models.user import User
from app.models.product import Product, RetailerOffer
from app.core.currency import rupees_to_paise


@pytest.fixture
def seeded_catalogue(db_session):
    """Seed test database with sample products and offers."""
    # Product 1: Headphones with 3 offers
    p1 = Product(
        title="Sony WH-1000XM5 Wireless Headphones",
        description="Premium noise cancelling headphones",
        category="Audio",
        brand="Sony",
        image_url="https://example.com/xm5.jpg",
        is_active=True,
        is_demo_data=True
    )
    # Product 2: Smartwatch
    p2 = Product(
        title="Apple Watch Series 9 GPS 45mm",
        description="Advanced smartwatch",
        category="Wearables",
        brand="Apple",
        image_url="https://example.com/watch.jpg",
        is_active=True,
        is_demo_data=True
    )
    # Product 3: Inactive product (should be hidden from public)
    p3 = Product(
        title="Discontinued Gadget Pro",
        description="Inactive item",
        category="Electronics",
        brand="OldBrand",
        is_active=False,
        is_demo_data=True
    )
    db_session.add_all([p1, p2, p3])
    db_session.flush()

    # Offers for Product 1:
    # Offer A: Lower price ₹25,999 but high shipping ₹500 -> Total ₹26,499
    o1_a = RetailerOffer(
        product_id=p1.id,
        retailer_name="SonicSound Store",
        product_price_paise=2599900,
        shipping_cost_paise=50000,
        is_shipping_known=True,
        total_cost_paise=2649900,
        estimated_delivery_days=3,
        retailer_rating_tenth=44,
        review_count=310,
        stock_status="in_stock",
        is_active=True,
        is_demo_data=True
    )
    # Offer B: Advertised price ₹26,000 with FREE shipping (0) -> Total ₹26,000 (CHEAPEST TOTAL)
    o1_b = RetailerOffer(
        product_id=p1.id,
        retailer_name="ElectroMart",
        product_price_paise=2600000,
        shipping_cost_paise=0,
        is_shipping_known=True,
        total_cost_paise=2600000,
        estimated_delivery_days=2,
        retailer_rating_tenth=48,
        review_count=900,
        stock_status="in_stock",
        is_active=True,
        is_demo_data=True
    )
    # Offer C: Unknown shipping (unconfirmed total cost)
    o1_c = RetailerOffer(
        product_id=p1.id,
        retailer_name="UnknownShipper Deals",
        product_price_paise=2400000,  # Advertised low, but shipping unknown!
        shipping_cost_paise=None,
        is_shipping_known=False,
        total_cost_paise=None,
        estimated_delivery_days=5,
        retailer_rating_tenth=40,
        review_count=50,
        stock_status="in_stock",
        is_active=True,
        is_demo_data=True
    )
    # Offer D: Inactive offer (should be hidden)
    o1_d = RetailerOffer(
        product_id=p1.id,
        retailer_name="Hidden Retailer",
        product_price_paise=2000000,
        shipping_cost_paise=0,
        is_shipping_known=True,
        total_cost_paise=2000000,
        stock_status="in_stock",
        is_active=False,
        is_demo_data=True
    )

    db_session.add_all([o1_a, o1_b, o1_c, o1_d])
    db_session.commit()
    return {"p1": p1, "p2": p2, "p3": p3}


@pytest.fixture
def auth_tokens(db_session):
    """Create a normal user and an admin user and return their tokens."""
    normal_user = User(
        email="shopper@test.com",
        hashed_password=hash_password("Pass1234!"),
        full_name="Shopper Test",
        role="user",
        is_active=True
    )
    admin_user = User(
        email="admin_catalogue@test.com",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Admin Catalogue",
        role="admin",
        is_active=True
    )
    db_session.add_all([normal_user, admin_user])
    db_session.commit()

    return {
        "user_token": create_access_token(subject=normal_user.id, role="user"),
        "admin_token": create_access_token(subject=admin_user.id, role="admin"),
        "user_id": normal_user.id,
        "admin_id": admin_user.id
    }


# =============================================================================
# 1. Product Catalogue & Search Tests
# =============================================================================

def test_list_products_excludes_inactive(api_client, seeded_catalogue):
    response = api_client.get("/api/products")
    assert response.status_code == 200
    data = response.json()
    titles = [p["title"] for p in data]

    assert "Sony WH-1000XM5 Wireless Headphones" in titles
    assert "Apple Watch Series 9 GPS 45mm" in titles
    # Discontinued/inactive product must be hidden
    assert "Discontinued Gadget Pro" not in titles


def test_list_products_filter_by_category(api_client, seeded_catalogue):
    response = api_client.get("/api/products?category=Audio")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["category"] == "Audio"
    assert data[0]["brand"] == "Sony"


def test_product_search_model_precision(api_client, seeded_catalogue):
    # Searching 'XM5' should find Sony headphones
    resp1 = api_client.get("/api/products/search?q=XM5")
    assert resp1.status_code == 200
    results1 = resp1.json()
    assert len(results1) == 1
    assert results1[0]["brand"] == "Sony"

    # Searching 'Series 9' should find Apple Watch and not Sony
    resp2 = api_client.get("/api/products/search?q=Series 9")
    assert resp2.status_code == 200
    results2 = resp2.json()
    assert len(results2) == 1
    assert results2[0]["brand"] == "Apple"

    # Searching non-existent model
    resp3 = api_client.get("/api/products/search?q=Pixel 8 Pro NonExistent")
    assert resp3.status_code == 200
    assert len(resp3.json()) == 0


def test_get_product_detail(api_client, seeded_catalogue):
    p1 = seeded_catalogue["p1"]
    response = api_client.get(f"/api/products/{p1.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == p1.id
    assert data["title"] == p1.title
    # Check that inactive offers are excluded
    retailer_names = [o["retailer_name"] for o in data["offers"]]
    assert "Hidden Retailer" not in retailer_names
    assert "ElectroMart" in retailer_names
    assert "SonicSound Store" in retailer_names


# =============================================================================
# 2. Price Comparison & Total Cost Landed Ranking Tests
# =============================================================================

def test_price_comparison_ranks_by_total_cost_not_advertised_price(api_client, seeded_catalogue):
    """Critical requirement: Total cost = Product price + Shipping.

    Advertised price trap:
    SonicSound has advertised price ₹25,999 with ₹500 shipping -> Total ₹26,499.
    ElectroMart has advertised price ₹26,000 with ₹0 shipping -> Total ₹26,000.
    ElectroMart MUST rank #1 even though its advertised product price is higher!
    """
    p1 = seeded_catalogue["p1"]
    response = api_client.get(f"/api/products/{p1.id}/offers")
    assert response.status_code == 200
    offers = response.json()

    # Confirmed offers must be ranked by total cost
    assert offers[0]["retailer_name"] == "ElectroMart"
    assert offers[0]["comparison_rank"] == 1
    assert offers[0]["total_cost_paise"] == 2600000  # ₹26,000.00
    assert "Rank 1: Lowest confirmed total cost" in offers[0]["rank_explanation"]

    assert offers[1]["retailer_name"] == "SonicSound Store"
    assert offers[1]["comparison_rank"] == 2
    assert offers[1]["total_cost_paise"] == 2649900  # ₹26,499.00
    assert "+₹499.00 more than Rank 1" in offers[1]["rank_explanation"]


def test_unknown_shipping_never_ranked_as_cheapest(api_client, seeded_catalogue):
    """Critical requirement: If shipping is unknown, do not assume free shipping

    and do not rank it as cheapest confirmed total!
    UnknownShipper has advertised ₹24,000 (lowest advertised), but shipping is unknown.
    It must be placed at the bottom with comparison_rank=None.
    """
    p1 = seeded_catalogue["p1"]
    response = api_client.get(f"/api/products/{p1.id}/offers")
    assert response.status_code == 200
    offers = response.json()

    unconfirmed_offer = next(o for o in offers if o["retailer_name"] == "UnknownShipper Deals")
    assert unconfirmed_offer["is_shipping_known"] is False
    assert unconfirmed_offer["comparison_rank"] is None
    assert unconfirmed_offer["total_cost_paise"] is None
    assert "Unranked: Shipping cost is unknown" in unconfirmed_offer["rank_explanation"]


# =============================================================================
# 3. Free AI Recommendation Engine Tests
# =============================================================================

def test_recommendation_requires_authentication(api_client, seeded_catalogue):
    p1 = seeded_catalogue["p1"]
    # Unauthenticated request rejected with 401
    resp = api_client.post("/api/recommendations", json={"product_id": p1.id})
    assert resp.status_code == 401


def test_recommendation_computes_cheapest_reliable_offer(api_client, seeded_catalogue, auth_tokens):
    headers = {"Authorization": f"Bearer {auth_tokens['user_token']}"}

    # Query by product name
    response = api_client.post(
        "/api/recommendations",
        json={"query": "Sony WH-1000XM5"},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()

    # Recommended winner is ElectroMart (lowest confirmed landed cost ₹26,000)
    winner = data["recommended_offer"]
    assert winner is not None
    assert winner["retailer_name"] == "ElectroMart"
    assert winner["total_cost_paise"] == 2600000
    assert data["ranking_position"] == 1

    # Rationale and savings explanation
    assert "recommends ElectroMart" in data["recommendation_summary"]
    assert "saves you ₹499.00 compared to the next closest option" in data["savings_explanation"]
    assert data["is_demo_data"] is True
    assert "Deterministic Intelligent Rule-Based Engine" in data["engine_type"]


def test_recommendation_by_product_id(api_client, seeded_catalogue, auth_tokens):
    headers = {"Authorization": f"Bearer {auth_tokens['user_token']}"}
    p1 = seeded_catalogue["p1"]

    response = api_client.post(
        "/api/recommendations",
        json={"product_id": p1.id},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["product"]["id"] == p1.id
    assert data["recommended_offer"]["retailer_name"] == "ElectroMart"


# =============================================================================
# 4. Protected Admin Catalogue Management Tests
# =============================================================================

def test_admin_product_crud_permissions(api_client, auth_tokens):
    user_headers = {"Authorization": f"Bearer {auth_tokens['user_token']}"}
    admin_headers = {"Authorization": f"Bearer {auth_tokens['admin_token']}"}

    product_payload = {
        "title": "Bose QuietComfort Ultra",
        "description": "High end audio",
        "category": "Audio",
        "brand": "Bose",
        "is_active": True
    }

    # 1. Normal user receives 403 Forbidden
    r_user = api_client.post("/api/admin/products", json=product_payload, headers=user_headers)
    assert r_user.status_code == 403

    # 2. Admin successfully creates product
    r_admin = api_client.post("/api/admin/products", json=product_payload, headers=admin_headers)
    assert r_admin.status_code == 201
    created_prod = r_admin.json()
    prod_id = created_prod["id"]
    assert created_prod["title"] == "Bose QuietComfort Ultra"

    # 3. Admin updates product
    r_update = api_client.put(
        f"/api/admin/products/{prod_id}",
        json={"title": "Bose QuietComfort Ultra (Updated)"},
        headers=admin_headers
    )
    assert r_update.status_code == 200
    assert r_update.json()["title"] == "Bose QuietComfort Ultra (Updated)"

    # 4. Admin toggles product status to inactive
    r_status = api_client.patch(
        f"/api/admin/products/{prod_id}/status?is_active=false",
        headers=admin_headers
    )
    assert r_status.status_code == 200
    assert r_status.json()["is_active"] is False


def test_admin_offer_creation_and_rejection_of_negative_amounts(api_client, seeded_catalogue, auth_tokens):
    admin_headers = {"Authorization": f"Bearer {auth_tokens['admin_token']}"}
    p1 = seeded_catalogue["p1"]

    # Reject negative price
    bad_payload = {
        "retailer_name": "ScamStore",
        "product_price": -500,
        "shipping_cost": 50
    }
    r_neg = api_client.post(
        f"/api/admin/products/{p1.id}/offers",
        json=bad_payload,
        headers=admin_headers
    )
    assert r_neg.status_code == 400
    assert "cannot be negative" in r_neg.json()["detail"].lower()

    # Create valid new offer
    valid_payload = {
        "retailer_name": "NewRetailer Alpha",
        "product_price": "25500.00",
        "shipping_cost": "200.00",
        "is_shipping_known": True,
        "estimated_delivery_days": 2,
        "retailer_rating_tenth": 46
    }
    r_valid = api_client.post(
        f"/api/admin/products/{p1.id}/offers",
        json=valid_payload,
        headers=admin_headers
    )
    assert r_valid.status_code == 201
    offer_data = r_valid.json()
    assert offer_data["product_price_paise"] == 2550000
    assert offer_data["shipping_cost_paise"] == 20000
    assert offer_data["total_cost_paise"] == 2570000
