"""Automated test suite for Stage 1 Copilot schemas and Gemini configuration normalization."""
import pytest
from pydantic import ValidationError
from app.core.config import Settings
from app.schemas.copilot import (
    CopilotQueryRequest,
    CopilotExtractedIntent,
    CopilotProductMatch,
    CopilotResponse,
)


# ==============================================================================
# 1. Gemini Configuration & Normalization Tests (Isolated instances)
# ==============================================================================

def test_gemini_key_missing_defaults_to_none():
    """Missing Gemini API key should evaluate to None."""
    custom_settings = Settings(GEMINI_API_KEY=None)
    assert custom_settings.GEMINI_API_KEY is None


def test_gemini_key_empty_string_normalized_to_none():
    """Empty string Gemini API key should normalize to None."""
    custom_settings = Settings(GEMINI_API_KEY="")
    assert custom_settings.GEMINI_API_KEY is None


def test_gemini_key_whitespace_only_normalized_to_none():
    """Whitespace-only Gemini API key should normalize to None."""
    custom_settings = Settings(GEMINI_API_KEY="   \t  \n  ")
    assert custom_settings.GEMINI_API_KEY is None


def test_gemini_key_non_empty_preserved_exactly():
    """Non-empty Gemini API key is preserved exactly as supplied."""
    test_key = "AIzaSyFakeKeyForTesting12345"
    custom_settings = Settings(GEMINI_API_KEY=test_key)
    assert custom_settings.GEMINI_API_KEY == test_key

    # Verifying exact preservation including internal/surrounding characters
    test_key_with_chars = "  AIzaSySurroundedKey  "
    custom_settings_surrounded = Settings(GEMINI_API_KEY=test_key_with_chars)
    assert custom_settings_surrounded.GEMINI_API_KEY == test_key_with_chars


def test_gemini_default_model_is_gemini_3_8_flash():
    """Default Gemini model should remain 'gemini-3.8-flash'."""
    custom_settings = Settings()
    assert custom_settings.GEMINI_MODEL == "gemini-3.8-flash"


# ==============================================================================
# 2. Copilot Schema & Validation Tests
# ==============================================================================

def test_copilot_response_independent_matched_products_lists():
    """Separate CopilotResponse instances receive independent mutable list instances."""
    intent = CopilotExtractedIntent(search_query="headphones")

    resp1 = CopilotResponse(
        query_message="Looking for headphones",
        extracted_intent=intent,
        matched_products_count=0,
        explanation="Search completed",
        copilot_mode="fallback_no_key"
    )
    resp2 = CopilotResponse(
        query_message="Looking for smartwatches",
        extracted_intent=intent,
        matched_products_count=0,
        explanation="Search completed",
        copilot_mode="fallback_no_key"
    )

    # Lists should be distinct objects in memory
    assert resp1.matched_products is not resp2.matched_products

    # Mutating resp1's list should not affect resp2
    dummy_match = CopilotProductMatch(
        id="prod-1",
        title="Test Headphones",
        category="Audio",
        brand="Sony"
    )
    resp1.matched_products.append(dummy_match)
    assert len(resp1.matched_products) == 1
    assert len(resp2.matched_products) == 0


def test_copilot_message_rejects_fewer_than_three_readable_characters():
    """Inquiry validation rejects strings with fewer than 3 readable characters."""
    with pytest.raises(ValidationError):
        CopilotQueryRequest(message="ab")

    with pytest.raises(ValidationError):
        CopilotQueryRequest(message="   a   ")

    with pytest.raises(ValidationError):
        CopilotQueryRequest(message="")


def test_copilot_message_removes_control_characters_and_normalizes_whitespace():
    """Message validation sanitizes ASCII control characters and collapses whitespace."""
    raw_message = "\x00\x08  Need   wireless\x1b  headphones \t\n under  28k  \x7f"
    req = CopilotQueryRequest(message=raw_message)
    assert req.message == "Need wireless headphones under 28k"


def test_copilot_budget_paise_conversion():
    """Budget in INR converts to exact integer paise without IEEE-754 drift."""
    intent = CopilotExtractedIntent(
        search_query="headphones",
        max_budget_rupees=28000
    )
    assert intent.max_budget_rupees == 28000
    assert intent.max_budget_paise == 2800000


def test_copilot_budget_limits_enforced():
    """Budgets below ₹100 and above ₹1,000,000 are rejected by schema validators."""
    # Valid bounds
    assert CopilotExtractedIntent(search_query="valid", max_budget_rupees=100).max_budget_rupees == 100
    assert CopilotExtractedIntent(search_query="valid", max_budget_rupees=1000000).max_budget_rupees == 1000000

    # Below minimum (ge=100)
    with pytest.raises(ValidationError):
        CopilotExtractedIntent(search_query="too low", max_budget_rupees=99)

    # Above maximum (le=1000000)
    with pytest.raises(ValidationError):
        CopilotExtractedIntent(search_query="too high", max_budget_rupees=1000001)


def test_copilot_key_features_maximum_count_enforced():
    """More than five key features are rejected."""
    # 5 features is allowed
    intent_5 = CopilotExtractedIntent(
        search_query="test",
        key_features=["f1", "f2", "f3", "f4", "f5"]
    )
    assert len(intent_5.key_features) == 5

    # 6 features is rejected
    with pytest.raises(ValidationError):
        CopilotExtractedIntent(
            search_query="test",
            key_features=["f1", "f2", "f3", "f4", "f5", "f6"]
        )


def test_copilot_unexpected_intent_fields_ignored():
    """Unexpected fields in AI output are safely discarded via extra='ignore'."""
    data = {
        "search_query": "noise cancelling headphones",
        "category": "Audio",
        "brand": "Sony",
        "max_budget_rupees": 28000,
        "key_features": ["anc", "bluetooth"],
        # Extra fields that must be ignored
        "invented_retailer": "Hallucinated Store",
        "invented_price": 19999,
        "hallucinated_product_id": "fake-1234"
    }
    intent = CopilotExtractedIntent.model_validate(data)
    dumped = intent.model_dump()

    assert intent.search_query == "noise cancelling headphones"
    assert "invented_retailer" not in dumped
    assert "invented_price" not in dumped
    assert "hallucinated_product_id" not in dumped
