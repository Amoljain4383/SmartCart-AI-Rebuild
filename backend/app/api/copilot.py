"""Public AI Shopping Copilot API Router.

Provides natural-language shopping query interpretation, multi-retailer offer ranking,
and true landed-cost recommendations.
"""
import time
from collections import defaultdict
from typing import Optional, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_optional_current_user
from app.models.user import User
from app.schemas.copilot import (
    CopilotQueryRequest,
    CopilotResponse,
)
from app.services.ai_copilot_service import (
    extract_shopping_intent,
    match_and_rank_catalog_products,
)

router = APIRouter(prefix="", tags=["Copilot"])

# In-memory sliding-window rate limiter
# Key: 'user:{user_id}' or 'ip:{client_host}' -> List of UNIX timestamps
# Note: Resets on application restart and is not shared across multi-process workers.
_rate_limit_store: Dict[str, List[float]] = defaultdict(list)
RATE_LIMIT_MAX_REQUESTS = 15
RATE_LIMIT_WINDOW_SECONDS = 60


def check_copilot_rate_limit(client_key: str) -> bool:
    """Check if the client has exceeded the 15 req/min sliding window rate limit."""
    now = time.time()
    cutoff = now - RATE_LIMIT_WINDOW_SECONDS
    # Purge timestamps outside the active sliding window
    active_timestamps = [t for t in _rate_limit_store[client_key] if t > cutoff]
    if len(active_timestamps) >= RATE_LIMIT_MAX_REQUESTS:
        _rate_limit_store[client_key] = active_timestamps
        return False

    active_timestamps.append(now)
    _rate_limit_store[client_key] = active_timestamps
    return True


@router.post(
    "",
    response_model=CopilotResponse,
    summary="Natural-language AI shopping copilot search"
)
async def query_copilot(
    request: CopilotQueryRequest,
    raw_request: Request,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Analyze a natural-language shopping inquiry, match catalogue items, and rank offers.

    Supports both guests and authenticated users.
    Applies strict in-memory rate limiting (max 15 inquiries/min).
    The backend remains 100% authoritative for all product pricing and offer ranking.
    """
    # 1. Rate-limiting key selection (User ID if authenticated, direct socket IP if guest)
    if current_user:
        client_key = f"user:{current_user.id}"
    else:
        # Use direct socket client.host; never trust unverified forwarded headers
        client_ip = raw_request.client.host if raw_request.client else "unknown_client"
        client_key = f"ip:{client_ip}"

    if not check_copilot_rate_limit(client_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Maximum 15 shopping inquiries per minute."
        )

    # 2. Extract shopping intent via Gemini REST or deterministic fallback
    intent, copilot_mode = await extract_shopping_intent(request.message)

    # 3. Match catalogue products and deterministically rank retailer offers
    matched_products, top_offer, explanation = match_and_rank_catalog_products(db, intent)

    # 4. Construct and return verified CopilotResponse
    return CopilotResponse(
        query_message=request.message,
        extracted_intent=intent,
        matched_products_count=len(matched_products),
        matched_products=matched_products,
        top_recommendation=top_offer,
        explanation=explanation,
        copilot_mode=copilot_mode,
        is_demo_data=True,
        notice="All product prices, shipping rates, and retailer offers are simulated demo data."
    )
