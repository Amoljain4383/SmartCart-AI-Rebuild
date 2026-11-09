"""AI Shopping Copilot Service.

Integrates with Google Gemini REST API using x-goog-api-key header for intent interpretation,
backed by an offline deterministic rule-based fallback parser.
All product matching, pricing, landed cost calculation, and offer ranking are strictly
performed by the backend database and deterministic recommendation engine.
"""
import re
import json
import logging
from typing import Tuple, List, Optional
import httpx
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.currency import paise_to_rupees_str
from app.models.product import Product, RetailerOffer
from app.schemas.copilot import (
    CopilotExtractedIntent,
    CopilotProductMatch,
    CopilotRecommendedOffer,
)
from app.services.recommendation_engine import (
    rank_and_explain_offers,
    generate_recommendation_summary,
)

logger = logging.getLogger("smartcart.copilot")

# Common brands and categories in demo catalogue
KNOWN_BRANDS = ["Sony", "Apple", "Logitech", "Amazon", "Dyson"]
KNOWN_CATEGORIES = {
    "Audio": ["headphone", "headphones", "earphone", "earphones", "earbud", "earbuds", "sound", "speaker"],
    "Wearables": ["watch", "smartwatch", "fitness tracker", "band"],
    "Accessories": ["mouse", "keyboard", "trackpad", "peripheral"],
    "Electronics": ["kindle", "ereader", "e-reader", "tablet", "reader"],
    "Home Appliances": ["vacuum", "cleaner", "vacuum cleaner", "appliance"],
}
KNOWN_FEATURES = [
    "noise cancelling",
    "active noise cancelling",
    "anc",
    "wireless",
    "bluetooth",
    "battery life",
    "battery",
    "quiet",
    "cordless",
    "gps",
    "waterproof",
    "ergonomic",
    "retina",
]

# Stop words to clean search queries
STOP_WORDS = {
    "i", "need", "want", "looking", "for", "search", "searching", "find",
    "show", "me", "a", "an", "the", "with", "and", "good", "best",
    "cheap", "cheapest", "college", "please", "buy", "purchase", "item", "product",
}


def extract_fallback_budget_rupees(text: str) -> Optional[int]:
    """Conservatively extract a user-specified budget cap in integer INR.

    Recognizes explicit budget language:
    - 'under 28000', 'under ₹28,000', 'under 28k', 'under 5k'
    - 'below ₹30,000', 'below 30k'
    - 'less than 15000'
    - 'within 60000', 'within ₹60,000'
    - 'budget of 35k', 'budget 20000'
    - 'up to 25000', 'max 40000'

    Crucially avoids false matches on product model numbers or alphanumeric codes
    (e.g. 'WH-1000XM5', '16GB RAM', 'Series 9', '4K').
    """
    # Regex requires explicit budget indicator or currency context before the number
    # Negative lookbehind ensures we are not inside a hyphenated/alphanumeric code like WH-1000
    pattern = r"""
        \b(?:under|below|less\s+than|within|budget(?:\s*of)?|up\s*to|max(?:imum)?(?:\s*of)?)\s*
        (?:₹|rs\.?|inr)?\s*
        (?<![\w-])(\d{1,3}(?:,\d{3})+|\d+)
        \s*(k|thousand)?\b
    """
    match = re.search(pattern, text, re.IGNORECASE | re.VERBOSE)
    if not match:
        # Check explicit currency prefix with trailing budget hint (e.g. '₹28,000 budget' or '₹28,000 max')
        alt_pattern = r"""
            \b(?:₹|rs\.?|inr)\s*
            (?<![\w-])(\d{1,3}(?:,\d{3})+|\d+)
            \s*(k|thousand)?\s*
            (?:budget|max|limit|or\s+less)\b
        """
        match = re.search(alt_pattern, text, re.IGNORECASE | re.VERBOSE)

    if not match:
        return None

    raw_val, multiplier = match.groups()
    cleaned = raw_val.replace(",", "")
    try:
        amount = int(cleaned)
        if multiplier and multiplier.lower() in ("k", "thousand"):
            amount *= 1000
        # Enforce valid shopping budget boundaries (₹100 to ₹1,000,000)
        if 100 <= amount <= 1000000:
            return amount
    except ValueError:
        pass
    return None


def deterministic_fallback_extraction(message: str) -> CopilotExtractedIntent:
    """Local offline rule-based parser when Gemini is unconfigured or unavailable."""
    msg_lower = message.lower()

    # 1. Budget extraction
    budget = extract_fallback_budget_rupees(message)

    # 2. Brand detection
    detected_brand = None
    for brand in KNOWN_BRANDS:
        if re.search(rf"\b{re.escape(brand.lower())}\b", msg_lower):
            detected_brand = brand
            break

    # 3. Category detection
    detected_category = None
    for category, keywords in KNOWN_CATEGORIES.items():
        if any(re.search(rf"\b{re.escape(kw)}\b", msg_lower) for kw in keywords):
            detected_category = category
            break

    # 4. Feature detection (max 5)
    detected_features = []
    for feature in KNOWN_FEATURES:
        if feature in msg_lower:
            detected_features.append(feature)
            if len(detected_features) == 5:
                break

    # 5. Clean query tokens
    # Remove extracted budget clauses to isolate the product inquiry
    cleaned_query = re.sub(
        r"\b(?:under|below|less\s+than|within|budget(?:\s*of)?|up\s*to|max(?:imum)?(?:\s*of)?)\s*(?:₹|rs\.?|inr)?\s*[\d,]+\s*(?:k|thousand)?\b",
        "",
        msg_lower,
        flags=re.IGNORECASE
    )
    cleaned_query = re.sub(r"[^\w\s-]", " ", cleaned_query)
    words = [w for w in cleaned_query.split() if w not in STOP_WORDS and len(w) > 1]
    search_query = " ".join(words).strip()
    if not search_query:
        search_query = detected_brand or detected_category or "product"

    summary = f"Searching for {search_query}"
    if budget:
        summary += f" under ₹{budget:,}"

    return CopilotExtractedIntent(
        search_query=search_query,
        category=detected_category,
        brand=detected_brand,
        max_budget_rupees=budget,
        key_features=detected_features,
        intent_summary=summary
    )


async def extract_shopping_intent(message: str) -> Tuple[CopilotExtractedIntent, str]:
    """Extract structured shopping intent using Gemini REST API or deterministic fallback.

    Never sends authentication, payment, or PII to Gemini.
    Never exposes API keys in URLs or logs.
    """
    if not settings.GEMINI_API_KEY:
        return deterministic_fallback_extraction(message), "fallback_no_key"

    gemini_prompt = (
        "You are an AI Shopping Assistant intent parser for an e-commerce platform.\n"
        "Your task is to analyze the user's shopping inquiry and output a structured JSON object.\n"
        "STRICT RULES:\n"
        "1. Extract ONLY user preferences: search_query, category, brand, max_budget_rupees, key_features, intent_summary.\n"
        "2. max_budget_rupees must be an integer in INR (e.g. 28000 for 28k or ₹28,000), or null if not specified.\n"
        "3. NEVER invent product IDs, retailer names, availability, prices, discounts, or shipping charges.\n"
        "4. Output MUST be valid JSON adhering exactly to the following schema:\n"
        "{\n"
        '  "search_query": "string (core product keywords)",\n'
        '  "category": "string or null (e.g. Audio, Wearables, Accessories, Electronics, Home Appliances)",\n'
        '  "brand": "string or null (e.g. Sony, Apple, Logitech, Amazon, Dyson)",\n'
        '  "max_budget_rupees": integer or null,\n'
        '  "key_features": ["array of up to 5 feature strings"],\n'
        '  "intent_summary": "short summary string"\n'
        "}\n\n"
        f"User Inquiry: {message}"
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent"
    headers = {
        "x-goog-api-key": settings.GEMINI_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": gemini_prompt}]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.1
        }
    }

    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.post(url, headers=headers, json=payload)

            if resp.status_code == 429:
                logger.warning("Gemini API rate limit reached (HTTP 429). Falling back to local parser.")
                return deterministic_fallback_extraction(message), "fallback_gemini_error"

            if resp.status_code in (401, 403):
                logger.warning(f"Gemini API auth error (HTTP {resp.status_code}). Falling back to local parser.")
                return deterministic_fallback_extraction(message), "fallback_gemini_error"

            if resp.is_error:
                logger.warning(f"Gemini API returned HTTP {resp.status_code}. Falling back to local parser.")
                return deterministic_fallback_extraction(message), "fallback_gemini_error"

            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                logger.warning("Gemini returned empty candidates. Falling back.")
                return deterministic_fallback_extraction(message), "fallback_invalid_response"

            raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            if not raw_text:
                return deterministic_fallback_extraction(message), "fallback_invalid_response"

            parsed_json = json.loads(raw_text)
            validated_intent = CopilotExtractedIntent.model_validate(parsed_json)
            return validated_intent, "gemini_ai"

    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        logger.warning(f"Gemini request failed ({type(exc).__name__}). Using deterministic fallback.")
        return deterministic_fallback_extraction(message), "fallback_gemini_error"
    except (json.JSONDecodeError, Exception) as exc:
        logger.warning(f"Gemini response parsing failed ({type(exc).__name__}). Using deterministic fallback.")
        return deterministic_fallback_extraction(message), "fallback_invalid_response"


def match_and_rank_catalog_products(
    db: Session,
    intent: CopilotExtractedIntent
) -> Tuple[List[CopilotProductMatch], Optional[CopilotRecommendedOffer], str]:
    """Search and rank actual catalogue products using the extracted intent.

    Guarantees:
    - Queries active products only.
    - Confirmed lowest landed cost is calculated solely from active offers with known shipping.
    - Unknown shipping is NEVER treated as free.
    - Excludes inactive offers and inactive products.
    - Strictly obeys budget cap in integer paise.
    - Never sorts by product.offers[0].total_cost_paise.
    """
    active_products = db.query(Product).filter(Product.is_active == True).all()
    if not active_products:
        return [], None, "No active products are currently available in the catalogue."

    matched_candidates: List[Tuple[Product, int, Optional[int]]] = []
    tokens = [t.lower() for t in re.split(r"[\s,]+", intent.search_query.strip()) if len(t) > 1 and t not in STOP_WORDS]

    for product in active_products:
        # Calculate lowest confirmed landed cost from active offers with known shipping
        confirmed_offers = [
            o for o in product.offers
            if getattr(o, "is_active", True) and o.is_shipping_known and o.total_cost_paise is not None
        ]
        min_landed_paise = min((o.total_cost_paise for o in confirmed_offers), default=None)

        # Budget constraint check:
        # If budget cap is set, a product with unknown/unconfirmed shipping cannot be confirmed under budget
        if intent.max_budget_paise is not None:
            if min_landed_paise is None or min_landed_paise > intent.max_budget_paise:
                continue

        # Relevance scoring
        score = 0
        haystack = f"{product.title} {product.brand} {product.category} {product.description or ''}".lower()

        # Category and Brand match bonuses
        if intent.brand and intent.brand.lower() in product.brand.lower():
            score += 30
        if intent.category and intent.category.lower() in product.category.lower():
            score += 25

        # Feature bonuses
        for feature in intent.key_features:
            if feature.lower() in haystack:
                score += 10

        # Token matches
        token_matches = 0
        for token in tokens:
            if token in haystack:
                score += 15
                token_matches += 1

        # Prevent false matches on isolated generic token overlap:
        # Must match either brand, category, or at least one meaningful token
        has_primary_match = (
            (intent.brand and intent.brand.lower() in product.brand.lower()) or
            (intent.category and intent.category.lower() in product.category.lower()) or
            (token_matches > 0)
        )

        if has_primary_match and score >= 15:
            matched_candidates.append((product, score, min_landed_paise))

    if not matched_candidates:
        budget_str = f" under ₹{intent.max_budget_rupees:,}" if intent.max_budget_rupees else ""
        return (
            [],
            None,
            f"No active products in our catalogue matched '{intent.search_query}'{budget_str}. "
            "Try broadening your search or exploring available categories."
        )

    # Sort matched candidates by:
    # 1. Relevance score descending
    # 2. Confirmed lowest landed cost ascending (products with confirmed cost first)
    matched_candidates.sort(
        key=lambda item: (
            -item[1],
            item[2] if item[2] is not None else float("inf")
        )
    )

    # Build ProductMatch list
    product_matches: List[CopilotProductMatch] = []
    for prod, _, min_paise in matched_candidates:
        min_formatted = paise_to_rupees_str(min_paise) if min_paise is not None else None
        product_matches.append(
            CopilotProductMatch(
                id=prod.id,
                title=prod.title,
                category=prod.category,
                brand=prod.brand,
                image_url=prod.image_url,
                min_total_cost_paise=min_paise,
                min_total_cost_formatted=min_formatted,
                offer_count=len([o for o in prod.offers if getattr(o, "is_active", True)]),
                is_demo_data=prod.is_demo_data
            )
        )

    # Deterministic top recommendation for the highest-ranked product
    top_product = matched_candidates[0][0]
    ranked_offers = rank_and_explain_offers(top_product.offers)
    winner, summary, savings = generate_recommendation_summary(top_product, ranked_offers)

    recommended_offer = None
    if winner and winner.is_shipping_known and winner.total_cost_paise is not None:
        recommended_offer = CopilotRecommendedOffer(
            product_id=top_product.id,
            product_title=top_product.title,
            offer_id=winner.id,
            recommended_retailer=winner.retailer_name,
            retailer_logo_url=winner.retailer_logo_url,
            product_price_formatted=winner.product_price_formatted,
            shipping_cost_formatted=winner.shipping_cost_formatted,
            landed_cost_formatted=winner.total_cost_formatted,
            landed_cost_paise=winner.total_cost_paise,
            savings_explanation=savings,
            delivery_days=winner.estimated_delivery_days,
            retailer_rating=winner.rating_float,
            review_count=winner.review_count,
            stock_status=winner.stock_status,
            is_shipping_known=winner.is_shipping_known,
            is_demo_data=True
        )
        explanation = f"SmartCart AI matched '{top_product.title}'. {summary}"
    else:
        explanation = f"Matched '{top_product.title}', but no confirmed active offers are currently available."

    return product_matches, recommended_offer, explanation
