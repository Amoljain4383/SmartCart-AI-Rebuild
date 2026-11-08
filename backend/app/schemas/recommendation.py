"""Pydantic schemas for Free AI Recommendation Engine."""
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.product import ProductResponse, RetailerOfferResponse


class RecommendationRequest(BaseModel):
    """User request for AI-driven cheapest reliable offer recommendation."""
    query: Optional[str] = Field(None, description="Product search keyword (e.g. 'Sony WH-1000XM5')")
    product_id: Optional[str] = Field(None, description="Direct product UUID")


class RecommendationResponse(BaseModel):
    """Transparent, deterministic rule-based recommendation response."""
    product: ProductResponse
    recommended_offer: Optional[RetailerOfferResponse] = None
    best_confirmed_total_cost_paise: Optional[int] = None
    best_confirmed_total_cost_formatted: Optional[str] = None
    all_offers: List[RetailerOfferResponse] = []
    ranking_position: int = 1
    recommendation_summary: str
    savings_explanation: Optional[str] = None
    is_demo_data: bool = True
    engine_type: str = "Deterministic Intelligent Rule-Based Engine (Free / Local)"
    notice: str = "All prices, shipping fees, and retailer offers are simulated demo data."
