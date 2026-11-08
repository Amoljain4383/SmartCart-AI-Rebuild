"""Pydantic schemas for Products, Retailer Offers, and Price Comparisons."""
from typing import List, Optional, Union
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.core.currency import paise_to_rupees_str, rupees_to_paise


class RetailerOfferResponse(BaseModel):
    """Public retailer offer representation with confirmed landed costs."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    product_id: str
    retailer_name: str
    retailer_logo_url: Optional[str] = None

    # Monetary values in integer paise
    product_price_paise: int
    product_price_formatted: str
    shipping_cost_paise: Optional[int] = None
    shipping_cost_formatted: str
    is_shipping_known: bool = True
    total_cost_paise: Optional[int] = None
    total_cost_formatted: str
    is_total_confirmed: bool = True

    # Performance and stock metrics
    estimated_delivery_days: int
    retailer_rating_tenth: int
    rating_float: float
    review_count: int
    return_policy: str
    stock_status: str
    offer_url: Optional[str] = None
    is_active: bool
    is_demo_data: bool
    comparison_rank: Optional[int] = None
    rank_explanation: Optional[str] = None


class ProductResponse(BaseModel):
    """Summary of a product item."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: Optional[str] = None
    category: str
    brand: str
    image_url: Optional[str] = None
    is_active: bool
    is_demo_data: bool = True
    offer_count: int = 0
    min_total_cost_paise: Optional[int] = None
    min_total_cost_formatted: Optional[str] = None


class ProductDetailResponse(ProductResponse):
    """Detailed product view with all competing retailer offers."""
    offers: List[RetailerOfferResponse] = []


class ProductCreateRequest(BaseModel):
    """Admin payload to create a new product."""
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    category: str = Field(..., min_length=2, max_length=100)
    brand: str = Field(..., min_length=1, max_length=100)
    image_url: Optional[str] = None
    is_active: bool = True


class ProductUpdateRequest(BaseModel):
    """Admin payload to update an existing product."""
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, min_length=2, max_length=100)
    brand: Optional[str] = Field(None, min_length=1, max_length=100)
    image_url: Optional[str] = None
    is_active: Optional[bool] = None


class OfferCreateRequest(BaseModel):
    """Admin payload to add a retailer offer to a product."""
    retailer_name: str = Field(..., min_length=2, max_length=100)
    retailer_logo_url: Optional[str] = None
    product_price: Union[str, int, float, Decimal] = Field(..., description="Product price in INR (e.g. 499.00 or 499)")
    shipping_cost: Optional[Union[str, int, float, Decimal]] = Field(None, description="Shipping cost in INR, or None if unknown")
    is_shipping_known: bool = True
    estimated_delivery_days: int = Field(3, ge=1, le=30)
    retailer_rating_tenth: int = Field(45, ge=10, le=50, description="45 = 4.5/5.0")
    review_count: int = Field(0, ge=0)
    return_policy: str = "14 days returnable"
    stock_status: str = "in_stock"
    offer_url: Optional[str] = None
    is_active: bool = True


class OfferUpdateRequest(BaseModel):
    """Admin payload to update an existing retailer offer."""
    retailer_name: Optional[str] = None
    retailer_logo_url: Optional[str] = None
    product_price: Optional[Union[str, int, float, Decimal]] = None
    shipping_cost: Optional[Union[str, int, float, Decimal]] = None
    is_shipping_known: Optional[bool] = None
    estimated_delivery_days: Optional[int] = Field(None, ge=1, le=30)
    retailer_rating_tenth: Optional[int] = Field(None, ge=10, le=50)
    review_count: Optional[int] = Field(None, ge=0)
    return_policy: Optional[str] = None
    stock_status: Optional[str] = None
    offer_url: Optional[str] = None
    is_active: Optional[bool] = None
