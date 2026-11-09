"""Comprehensive automated tests for Stage 2: AI Shopping Copilot and API."""
import re
import json
import uuid
import pytest
import httpx
from unittest.mock import patch, AsyncMock
from app.core.config import settings
from app.core.security import hash_password, create_access_token
from app.core.currency import rupees_to_paise
from app.models.user import User
from app.models.product import Product, RetailerOffer
from app.models.order import Order
from app.models.revoked_token import RevokedToken
from app.schemas.copilot import CopilotQueryRequest, CopilotExtractedIntent
from app.services.ai_copilot_service import (
    extract_shopping_intent,
    extract_fallback_budget_rupees,
    deterministic_fallback_extraction,
    match_and_rank_catalog_products,
)
from app.api.copilot import _rate_limit_store


@pytest.fixture(autouse=True)
def clear_rate_limit_store():
    """Ensure in-memory rate limiter store is fresh for every test."""
    _rate_limit_store.clear()
    yield
    _rate_limit_store.clear()


@pytest.fixture
def seeded_copilot_catalog(db_session):
    """Seed test database with realistic products and competing offers."""
    # Product 1: Sony Headphones (Active)
    p1 = Product(
        title="Sony WH-1000XM5 Wireless Noise Cancelling Headphones",
        description="Industry-leading noise cancellation with 30-hour battery life",
        category="Audio",
        brand="Sony",
        image_url="https://example.com/sony.jpg",
        is_active=True,
        is_demo_data=True
    )
    # Product 2: Apple Watch (Active)
    p2 = Product(
        title="Apple Watch Series 9 GPS 45mm",
        description="Smartwatch with advanced health tracking and retina display",
        category="Wearables",
        brand="Apple",
        image_url="https://example.com/apple.jpg",
        is_active=True,
        is_demo_data=True
    )
    # Product 3: Discontinued Mouse (Inactive)
    p3 = Product(
        title="Discontinued Pro Gaming Mouse",
        description="Old generation mouse",
        category="Accessories",
        brand="Logitech",
        is_active=False,
        is_demo_data=True
    )
    # Product 4: Budget Unconfirmed Shipping Product
    p4 = Product(
        title="Mystery Soundbar",
        description="Wireless soundbar with unknown shipping",
        category="Audio",
        brand="Sony",
        is_active=True,
        is_demo_data=True
    )
    db_session.add_all([p1, p2, p3, p4])
    db_session.flush()

    # Product 1 Offers:
    # Offer 1A: ₹25,999 + ₹499 shipping = ₹26,498 (Rank 1 winner)
    o1a = RetailerOffer(
        product_id=p1.id,
        retailer_name="SonicSound Store (Demo)",
        product_price_paise=rupees_to_paise("25999.00"),
        shipping_cost_paise=rupees_to_paise("499.00"),
        is_shipping_known=True,
        total_cost_paise=rupees_to_paise("26498.00"),
        estimated_delivery_days=4,
        retailer_rating_tenth=44,
        review_count=310,
        stock_status="in_stock",
        is_active=True,
        is_demo_data=True
    )
    # Offer 1B: ₹26,990 + ₹0 shipping = ₹26,990 (Rank 2)
    o1b = RetailerOffer(
        product_id=p1.id,
        retailer_name="ElectroMart India (Demo)",
        product_price_paise=rupees_to_paise("26990.00"),
        shipping_cost_paise=0,
        is_shipping_known=True,
        total_cost_paise=rupees_to_paise("26990.00"),
        estimated_delivery_days=2,
        retailer_rating_tenth=47,
        review_count=840,
        stock_status="in_stock",
        is_active=True,
        is_demo_data=True
    )
    # Offer 1C: Inactive offer (Must be ignored)
    o1c = RetailerOffer(
        product_id=p1.id,
        retailer_name="Inactive Fake Retailer",
        product_price_paise=rupees_to_paise("19999.00"),
        shipping_cost_paise=0,
        is_shipping_known=True,
        total_cost_paise=rupees_to_paise("19999.00"),
        estimated_delivery_days=1,
        retailer_rating_tenth=49,
        review_count=100,
        stock_status="in_stock",
        is_active=False,
        is_demo_data=True
    )

    # Product 2 Offers:
    o2a = RetailerOffer(
        product_id=p2.id,
        retailer_name="QuickCart Express (Simulated)",
        product_price_paise=rupees_to_paise("39999.00"),
        shipping_cost_paise=rupees_to_paise("750.00"),
        is_shipping_known=True,
        total_cost_paise=rupees_to_paise("40749.00"),
        estimated_delivery_days=3,
        retailer_rating_tenth=43,
        review_count=215,
        stock_status="in_stock",
        is_active=True,
        is_demo_data=True
    )

    # Product 4 Offers (Unknown shipping):
    o4a = RetailerOffer(
        product_id=p4.id,
        retailer_name="Unknown Shipping Store",
        product_price_paise=rupees_to_paise("5000.00"),
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

    db_session.add_all([o1a, o1b, o1c, o2a, o4a])
    db_session.commit()
    return {"p1": p1, "p2": p2, "p3": p3, "p4": p4}


# ==============================================================================
# SECTION A: Gemini Service Tests (1 - 11)
# ==============================================================================

@pytest.mark.asyncio
async def test_01_missing_key_invokes_fallback(monkeypatch):
    """Missing Gemini API key immediately invokes local fallback without HTTP call."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", None)
    intent, mode = await extract_shopping_intent("headphones under 28000")
    assert mode == "fallback_no_key"
    assert intent.max_budget_rupees == 28000
    assert "headphones" in intent.search_query.lower()


@pytest.mark.asyncio
async def test_02_empty_key_invokes_fallback(monkeypatch):
    """Empty string Gemini API key immediately invokes fallback."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    intent, mode = await extract_shopping_intent("Sony headphones below 30000")
    assert mode == "fallback_no_key"
    assert intent.max_budget_rupees == 30000


@pytest.mark.asyncio
async def test_03_successful_gemini_response(monkeypatch):
    """Valid Gemini HTTP 200 JSON produces structured CopilotExtractedIntent."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "AIzaSyTestKey123")
    mock_payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps({
                                "search_query": "headphones noise cancelling",
                                "category": "Audio",
                                "brand": "Sony",
                                "max_budget_rupees": 28000,
                                "key_features": ["noise cancelling", "wireless"],
                                "intent_summary": "Looking for Sony noise cancelling headphones under ₹28,000"
                            })
                        }
                    ]
                }
            }
        ]
    }

    mock_resp = httpx.Response(200, json=mock_payload, request=httpx.Request("POST", "https://api.google.com"))
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        intent, mode = await extract_shopping_intent("Sony headphones under 28k")

        assert mode == "gemini_ai"
        assert intent.category == "Audio"
        assert intent.brand == "Sony"
        assert intent.max_budget_rupees == 28000
        assert intent.max_budget_paise == 2800000


@pytest.mark.asyncio
async def test_04_gemini_401_invokes_fallback(monkeypatch):
    """Gemini 401 Unauthorized invokes fallback without raising exception."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "invalid_key")
    mock_resp = httpx.Response(401, json={"error": "Invalid API key"}, request=httpx.Request("POST", "https://api.google.com"))
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        intent, mode = await extract_shopping_intent("headphones under 28000")
        assert mode == "fallback_gemini_error"
        assert intent.max_budget_rupees == 28000


@pytest.mark.asyncio
async def test_05_gemini_403_invokes_fallback(monkeypatch):
    """Gemini 403 Forbidden invokes fallback safely."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "restricted_key")
    mock_resp = httpx.Response(403, json={"error": "Permission denied"}, request=httpx.Request("POST", "https://api.google.com"))
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        intent, mode = await extract_shopping_intent("smartwatch under 40000")
        assert mode == "fallback_gemini_error"
        assert intent.max_budget_rupees == 40000


@pytest.mark.asyncio
async def test_06_gemini_429_invokes_fallback(monkeypatch):
    """Gemini 429 Rate Limit invokes fallback seamlessly."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test_key")
    mock_resp = httpx.Response(429, json={"error": "Resource exhausted"}, request=httpx.Request("POST", "https://api.google.com"))
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        intent, mode = await extract_shopping_intent("wireless mouse under 5k")
        assert mode == "fallback_gemini_error"
        assert intent.max_budget_rupees == 5000


@pytest.mark.asyncio
async def test_07_gemini_timeout_invokes_fallback(monkeypatch):
    """Gemini request timeout cleanly triggers fallback."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test_key")
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.TimeoutException("Timed out after 4.0s")
        intent, mode = await extract_shopping_intent("kindle under 15000")
        assert mode == "fallback_gemini_error"
        assert intent.max_budget_rupees == 15000


@pytest.mark.asyncio
async def test_08_gemini_invalid_json_invokes_fallback(monkeypatch):
    """Non-JSON response text from Gemini triggers fallback_invalid_response."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test_key")
    mock_payload = {
        "candidates": [
            {"content": {"parts": [{"text": "I think you want headphones..."}]}}
        ]
    }
    mock_resp = httpx.Response(200, json=mock_payload, request=httpx.Request("POST", "https://api.google.com"))
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        intent, mode = await extract_shopping_intent("headphones under 28000")
        assert mode == "fallback_invalid_response"
        assert intent.max_budget_rupees == 28000


@pytest.mark.asyncio
async def test_09_gemini_missing_required_fields_invokes_fallback(monkeypatch):
    """Gemini output missing search_query field triggers fallback."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test_key")
    mock_payload = {
        "candidates": [
            {"content": {"parts": [{"text": json.dumps({"category": "Audio"})}]}}
        ]
    }
    mock_resp = httpx.Response(200, json=mock_payload, request=httpx.Request("POST", "https://api.google.com"))
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        intent, mode = await extract_shopping_intent("headphones under 28000")
        assert mode == "fallback_invalid_response"
        assert intent.max_budget_rupees == 28000


@pytest.mark.asyncio
async def test_10_api_key_sent_in_header_not_url(monkeypatch):
    """API key is strictly provided in x-goog-api-key header and NOT in the URL."""
    fake_secret_key = "AIzaSySecretDoNotLeak12345"
    monkeypatch.setattr(settings, "GEMINI_API_KEY", fake_secret_key)

    mock_resp = httpx.Response(
        200,
        json={"candidates": [{"content": {"parts": [{"text": json.dumps({"search_query": "headphones"})}]}}]},
        request=httpx.Request("POST", "https://api.google.com")
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        await extract_shopping_intent("test headphones")

        call_args, call_kwargs = mock_post.call_args
        target_url = call_args[0]
        headers = call_kwargs.get("headers", {})

        # Key must NOT appear in URL query string
        assert fake_secret_key not in target_url
        assert "key=" not in target_url
        # Key must be in header
        assert headers.get("x-goog-api-key") == fake_secret_key


@pytest.mark.asyncio
async def test_11_api_key_never_in_response_or_logs(monkeypatch, caplog):
    """API key is never serialized into response models or recorded in logger messages."""
    fake_secret_key = "AIzaSySuperSecretKey999"
    monkeypatch.setattr(settings, "GEMINI_API_KEY", fake_secret_key)

    mock_resp = httpx.Response(401, json={"error": "unauthorized"}, request=httpx.Request("POST", "https://api.google.com"))
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        intent, mode = await extract_shopping_intent("Sony headphones under 28k")

        # Key must not appear in intent model dump
        assert fake_secret_key not in json.dumps(intent.model_dump())
        # Key must not appear in any log output
        for record in caplog.records:
            assert fake_secret_key not in record.message


# ==============================================================================
# SECTION B: Fallback Parser Tests (12 - 18)
# ==============================================================================

def test_12_fallback_under_28000():
    """Extracts 'under 28000' correctly."""
    intent = deterministic_fallback_extraction("wireless headphones under 28000")
    assert intent.max_budget_rupees == 28000
    assert "headphones" in intent.search_query.lower()


def test_13_fallback_below_rupees_30000():
    """Extracts 'below ₹30,000' with currency symbol and comma."""
    intent = deterministic_fallback_extraction("Sony headphones below ₹30,000")
    assert intent.max_budget_rupees == 30000
    assert intent.brand == "Sony"


def test_14_fallback_under_5k():
    """Extracts 'under 5k' metric notation."""
    intent = deterministic_fallback_extraction("gaming mouse under 5k")
    assert intent.max_budget_rupees == 5000
    assert "mouse" in intent.search_query.lower()


def test_15_fallback_within_60000():
    """Extracts 'within 60000' syntax."""
    intent = deterministic_fallback_extraction("laptop within 60000")
    assert intent.max_budget_rupees == 60000


def test_16_fallback_model_number_not_accidental_budget():
    """WH-1000XM5 model number is NOT interpreted as an accidental budget."""
    intent = deterministic_fallback_extraction("Sony WH-1000XM5 wireless headphones")
    assert intent.max_budget_rupees is None
    assert "wh-1000xm5" in intent.search_query.lower()

    # Also test alphanumeric specs like 16GB
    intent_ram = deterministic_fallback_extraction("laptop with 16GB RAM under 60000")
    assert intent_ram.max_budget_rupees == 60000


def test_17_fallback_queries_without_budget_return_none():
    """Queries lacking budget language return None for budget."""
    intent = deterministic_fallback_extraction("Apple smartwatch with heart rate tracking")
    assert intent.max_budget_rupees is None
    assert intent.brand == "Apple"
    assert intent.category == "Wearables"


def test_18_fallback_conservative_features_and_brand():
    """Extracts known features and brands conservatively."""
    intent = deterministic_fallback_extraction("Sony noise cancelling headphones with long battery life")
    assert intent.brand == "Sony"
    assert "noise cancelling" in intent.key_features
    assert "battery life" in intent.key_features or "battery" in intent.key_features
    assert len(intent.key_features) <= 5


# ==============================================================================
# SECTION C: Product Matching & Landed Cost Integrity (19 - 25)
# ==============================================================================

def test_19_match_active_catalogue_products(db_session, seeded_copilot_catalog):
    """Matches active product Sony WH-1000XM5 within ₹28,000 budget."""
    intent = CopilotExtractedIntent(
        search_query="Sony headphones",
        category="Audio",
        brand="Sony",
        max_budget_rupees=28000
    )
    matches, top_offer, explanation = match_and_rank_catalog_products(db_session, intent)
    assert len(matches) == 1
    assert matches[0].title == "Sony WH-1000XM5 Wireless Noise Cancelling Headphones"
    assert top_offer is not None
    assert top_offer.recommended_retailer == "SonicSound Store (Demo)"
    assert top_offer.landed_cost_formatted == "₹26,498.00"


def test_20_exclude_inactive_products(db_session, seeded_copilot_catalog):
    """Inactive products are never matched or returned."""
    intent = CopilotExtractedIntent(
        search_query="Pro Gaming Mouse",
        category="Accessories",
        brand="Logitech"
    )
    matches, top_offer, explanation = match_and_rank_catalog_products(db_session, intent)
    # Product 3 is inactive, so zero matches
    assert len(matches) == 0
    assert top_offer is None


def test_21_avoid_unrelated_token_matches(db_session, seeded_copilot_catalog):
    """Does not match smartwatches when user searches for vacuum cleaners."""
    intent = CopilotExtractedIntent(
        search_query="cordless vacuum cleaner",
        category="Home Appliances",
        brand="Dyson"
    )
    matches, top_offer, _ = match_and_rank_catalog_products(db_session, intent)
    assert len(matches) == 0


def test_22_confirmed_landed_cost_calculation(db_session, seeded_copilot_catalog):
    """Ranks by confirmed landed cost (price + shipping), not sticker price."""
    intent = CopilotExtractedIntent(
        search_query="Sony headphones",
        category="Audio"
    )
    matches, top_offer, explanation = match_and_rank_catalog_products(db_session, intent)
    # SonicSound Store has sticker ₹25,999 + ₹499 shipping = ₹26,498
    # ElectroMart has sticker ₹26,990 + ₹0 shipping = ₹26,990
    # SonicSound Store must win because ₹26,498 < ₹26,990
    assert top_offer.recommended_retailer == "SonicSound Store (Demo)"
    assert top_offer.landed_cost_paise == 2649800


def test_23_unknown_shipping_never_treated_as_free(db_session, seeded_copilot_catalog):
    """Product with unknown shipping cannot be confirmed as under budget."""
    intent = CopilotExtractedIntent(
        search_query="Mystery Soundbar",
        category="Audio",
        max_budget_rupees=10000
    )
    matches, top_offer, explanation = match_and_rank_catalog_products(db_session, intent)
    # Product 4 only has unknown shipping offer, so it has no confirmed landed cost
    # Budget filter must drop it
    assert len(matches) == 0
    assert top_offer is None


def test_24_inactive_offers_excluded(db_session, seeded_copilot_catalog):
    """Inactive offers (Offer 1C at ₹19,999) are excluded from ranking."""
    intent = CopilotExtractedIntent(
        search_query="Sony headphones",
        category="Audio"
    )
    _, top_offer, _ = match_and_rank_catalog_products(db_session, intent)
    # Inactive fake retailer offer at ₹19,999 must NOT be selected
    assert top_offer.recommended_retailer != "Inactive Fake Retailer"
    assert top_offer.landed_cost_paise == 2649800


def test_25_empty_catalogue_result_handled_gracefully(db_session):
    """Empty catalogue returns helpful message without exceptions."""
    intent = CopilotExtractedIntent(
        search_query="4K OLED Gaming Monitor",
        max_budget_rupees=10000
    )
    matches, top_offer, explanation = match_and_rank_catalog_products(db_session, intent)
    assert len(matches) == 0
    assert top_offer is None
    assert "No active products" in explanation


# ==============================================================================
# SECTION D: API Security, Auth & Rate Limiting (26 - 31)
# ==============================================================================

def test_26_guest_requests_work(api_client, db_session, seeded_copilot_catalog):
    """Unauthenticated guest requests successfully query the copilot."""
    response = api_client.post(
        "/api/copilot",
        json={"message": "wireless headphones under 28000"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["query_message"] == "wireless headphones under 28000"
    assert data["matched_products_count"] == 1
    assert data["top_recommendation"]["recommended_retailer"] == "SonicSound Store (Demo)"
    assert data["is_demo_data"] is True


def test_27_authenticated_requests_work(api_client, db_session, seeded_copilot_catalog):
    """Authenticated user requests are recognized and processed."""
    user = User(
        email="shopper@test.local",
        hashed_password=hash_password("Password123!"),
        full_name="Test Shopper",
        role="user",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token(subject=user.id, role="user")
    response = api_client.post(
        "/api/copilot",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Apple smartwatch under 45000"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["matched_products_count"] >= 1
    assert data["top_recommendation"]["product_title"] == "Apple Watch Series 9 GPS 45mm"


def test_28_revoked_tokens_rejected(api_client, db_session):
    """Revoked JWT bearer tokens are rejected with HTTP 401."""
    user = User(
        email="revoked@test.local",
        hashed_password=hash_password("Password123!"),
        full_name="Revoked User",
        role="user",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()

    custom_jti = str(uuid.uuid4())
    token = create_access_token(subject=user.id, role="user", custom_jti=custom_jti)

    # Revoke the token
    revocation = RevokedToken(jti=custom_jti, expires_at=db_session.execute(
        User.__table__.select()
    ).context.engine.dialect.name and None or "2099-01-01 00:00:00")
    # Add to revoked_tokens table using model
    from datetime import datetime, timezone, timedelta
    rev_record = RevokedToken(jti=custom_jti, expires_at=datetime.now(timezone.utc) + timedelta(hours=1))
    db_session.add(rev_record)
    db_session.commit()

    response = api_client.post(
        "/api/copilot",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "wireless headphones"}
    )
    assert response.status_code == 401
    assert "revoked" in response.json()["detail"].lower()


def test_29_rate_limit_exceeded_returns_429(api_client, seeded_copilot_catalog):
    """Exceeding 15 requests per minute returns HTTP 429."""
    # Send 15 requests (allowed)
    for _ in range(15):
        resp = api_client.post(
            "/api/copilot",
            json={"message": "wireless headphones"}
        )
        assert resp.status_code == 200

    # 16th request must trigger HTTP 429
    excess_resp = api_client.post(
        "/api/copilot",
        json={"message": "wireless headphones"}
    )
    assert excess_resp.status_code == 429
    assert "rate limit exceeded" in excess_resp.json()["detail"].lower()


def test_30_request_validation_works(api_client):
    """Validation rejects messages shorter than 3 readable characters."""
    resp_short = api_client.post("/api/copilot", json={"message": "ab"})
    assert resp_short.status_code == 422

    resp_empty = api_client.post("/api/copilot", json={"message": "   "})
    assert resp_empty.status_code == 422


def test_31_no_paypal_order_created_by_copilot(api_client, db_session, seeded_copilot_catalog):
    """Calling the Copilot endpoint performs zero database mutations on orders or payments."""
    initial_orders_count = db_session.query(Order).count()
    assert initial_orders_count == 0

    response = api_client.post(
        "/api/copilot",
        json={"message": "Sony headphones under 28000"}
    )
    assert response.status_code == 200

    # Verify zero orders were created
    orders_after = db_session.query(Order).count()
    assert orders_after == 0
