"""Pydantic schemas registry."""
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
    MessageResponse,
    AdminDashboardResponse,
)
from app.schemas.product import (
    ProductResponse,
    ProductDetailResponse,
    ProductCreateRequest,
    ProductUpdateRequest,
    RetailerOfferResponse,
    OfferCreateRequest,
    OfferUpdateRequest,
)
from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
)
from app.schemas.order import (
    OrderItemCreate,
    OrderCreateRequest,
    OrderItemResponse,
    OrderResponse,
    PayPalOrderCreateResponse,
    PayPalCaptureResponse,
)

__all__ = [
    "UserRegisterRequest",
    "UserLoginRequest",
    "UserResponse",
    "TokenResponse",
    "MessageResponse",
    "AdminDashboardResponse",
    "ProductResponse",
    "ProductDetailResponse",
    "ProductCreateRequest",
    "ProductUpdateRequest",
    "RetailerOfferResponse",
    "OfferCreateRequest",
    "OfferUpdateRequest",
    "RecommendationRequest",
    "RecommendationResponse",
    "OrderItemCreate",
    "OrderCreateRequest",
    "OrderItemResponse",
    "OrderResponse",
    "PayPalOrderCreateResponse",
    "PayPalCaptureResponse",
]
