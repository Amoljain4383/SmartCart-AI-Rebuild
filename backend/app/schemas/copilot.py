"""Pydantic schemas for SmartCart AI Shopping Copilot.

Enforces strict validation on natural-language user queries, structured intent extraction,
budget limits, and grounded recommendation responses.
"""
import re
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class CopilotQueryRequest(BaseModel):
    """Incoming user natural-language shopping inquiry."""
    message: str = Field(
        ...,
        min_length=3,
        max_length=300,
        description="User shopping inquiry in natural language (e.g. 'Wireless headphones under 28k')"
    )

    @field_validator("message")
    @classmethod
    def sanitize_message(cls, v: str) -> str:
        """Strip control characters, null bytes, and normalize excessive whitespace."""
        # Remove ASCII control characters (0-31, 127)
        cleaned = re.sub(r"[\x00-\x1f\x7f]", "", v)
        # Collapse multiple spaces into single space
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if len(cleaned) < 3:
            raise ValueError("Inquiry must contain at least 3 readable characters.")
        return cleaned


class CopilotExtractedIntent(BaseModel):
    """Structured search intent extracted from natural language.

    Strictly ignores unexpected fields from AI models to prevent injection of
    invented products, retailers, prices, or inventory counts.
    """
    model_config = ConfigDict(extra="ignore")

    search_query: str = Field(
        ...,
        min_length=1,
        max_length=150,
        description="Core keyword search tokens extracted from the user inquiry"
    )
    category: Optional[str] = Field(
        None,
        max_length=50,
        description="Target product category hint (e.g., 'Audio', 'Electronics', 'Wearables')"
    )
    brand: Optional[str] = Field(
        None,
        max_length=50,
        description="Target brand hint (e.g., 'Sony', 'Apple', 'Logitech')"
    )
    max_budget_rupees: Optional[int] = Field(
        None,
        ge=100,
        le=1000000,
        description="Maximum budget cap in INR (100 to 1,000,000)"
    )
    key_features: List[str] = Field(
        default_factory=list,
        max_length=5,
        description="List of requested features (maximum 5 items)"
    )
    intent_summary: Optional[str] = Field(
        None,
        max_length=255,
        description="Brief natural language summary of the detected shopping intent"
    )

    @property
    def max_budget_paise(self) -> Optional[int]:
        """Convert rupee budget to integer paise for zero-float arithmetic."""
        if self.max_budget_rupees is not None:
            return self.max_budget_rupees * 100
        return None


class CopilotProductMatch(BaseModel):
    """Summary of a verified catalogue product matched by the copilot."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    category: str
    brand: str
    image_url: Optional[str] = None
    min_total_cost_paise: Optional[int] = None
    min_total_cost_formatted: Optional[str] = None
    offer_count: int = 0
    is_demo_data: bool = True


class CopilotRecommendedOffer(BaseModel):
    """Authoritative top recommended offer derived deterministically from the database."""
    product_id: str
    product_title: str
    offer_id: str
    recommended_retailer: str
    retailer_logo_url: Optional[str] = None
    product_price_formatted: str
    shipping_cost_formatted: str
    landed_cost_formatted: str
    landed_cost_paise: int
    savings_explanation: Optional[str] = None
    delivery_days: int
    retailer_rating: float
    review_count: int
    stock_status: str = "in_stock"
    is_shipping_known: bool = True
    is_demo_data: bool = True


class CopilotResponse(BaseModel):
    """Complete structured response delivered to the frontend copilot component."""
    query_message: str
    extracted_intent: CopilotExtractedIntent
    matched_products_count: int
    matched_products: List[CopilotProductMatch] = Field(default_factory=list)
    top_recommendation: Optional[CopilotRecommendedOffer] = None
    explanation: str
    copilot_mode: str = Field(
        ...,
        description="Mode indicator: 'gemini_ai', 'fallback_deterministic', 'fallback_no_key', etc."
    )
    is_demo_data: bool = True
    notice: str = "All product prices, shipping rates, and retailer offers are simulated demo data."
