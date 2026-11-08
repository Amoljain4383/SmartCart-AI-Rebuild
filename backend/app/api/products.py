"""Public Product Catalogue and Offer Comparison API routes."""
import re
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.core.database import get_db
from app.models.product import Product, RetailerOffer
from app.schemas.product import ProductResponse, ProductDetailResponse, RetailerOfferResponse
from app.services.recommendation_engine import rank_and_explain_offers
from app.core.currency import paise_to_rupees_str

router = APIRouter(prefix="", tags=["Products"])


def _build_product_summary(product: Product) -> ProductResponse:
    """Helper to convert a Product ORM entity into ProductResponse with offer count and min cost."""
    active_offers = [
        o for o in product.offers
        if getattr(o, "is_active", True) and o.is_shipping_known and o.total_cost_paise is not None
    ]
    min_paise = min((o.total_cost_paise for o in active_offers), default=None)
    min_formatted = paise_to_rupees_str(min_paise) if min_paise is not None else None

    return ProductResponse(
        id=product.id,
        title=product.title,
        description=product.description,
        category=product.category,
        brand=product.brand,
        image_url=product.image_url,
        is_active=product.is_active,
        is_demo_data=product.is_demo_data,
        offer_count=len(product.offers),
        min_total_cost_paise=min_paise,
        min_total_cost_formatted=min_formatted
    )


@router.get(
    "",
    response_model=List[ProductResponse],
    summary="List active catalog products with optional filters and sorting"
)
def list_products(
    category: Optional[str] = Query(None, description="Filter by product category"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    sort_by: Optional[str] = Query("title", description="Sort by: 'title', 'price_asc', 'price_desc'"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Retrieve catalog products available for customer search and comparison.

    Strictly excludes inactive products.
    """
    query = db.query(Product).filter(Product.is_active == True)

    if category:
        query = query.filter(Product.category.ilike(f"%{category.strip()}%"))
    if brand:
        query = query.filter(Product.brand.ilike(f"%{brand.strip()}%"))

    if sort_by == "title":
        query = query.order_by(Product.title.asc())

    products = query.offset(skip).limit(limit).all()
    summaries = [_build_product_summary(p) for p in products]

    if sort_by == "price_asc":
        summaries.sort(key=lambda p: (p.min_total_cost_paise is None, p.min_total_cost_paise or 0))
    elif sort_by == "price_desc":
        summaries.sort(key=lambda p: (p.min_total_cost_paise is None, -(p.min_total_cost_paise or 0)))

    return summaries


@router.get(
    "/search",
    response_model=List[ProductResponse],
    summary="Search products with strict model specification precision"
)
def search_products(
    q: str = Query(..., min_length=1, description="Search query string"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Search products avoiding ambiguous duplicate model collisions.

    Disaggregates queries to prevent conflating distinct model specifications
    (e.g., Apple Watch Series 9 vs Series 8, Sony XM5 vs XM4).
    """
    clean_q = q.strip()
    if not clean_q:
        return []

    tokens = [t.lower() for t in re.split(r"\s+", clean_q) if len(t) > 0]

    # Base query for active products
    base_query = db.query(Product).filter(Product.is_active == True)
    all_active = base_query.all()

    matched: List[Product] = []
    for product in all_active:
        haystack = f"{product.title} {product.brand} {product.category} {product.description or ''}".lower()
        # Require all significant search tokens to be present
        if all(token in haystack for token in tokens):
            matched.append(product)

    # Convert to response summaries
    summaries = [_build_product_summary(p) for p in matched]
    return summaries[skip: skip + limit]


@router.get(
    "/{product_id}",
    response_model=ProductDetailResponse,
    summary="Retrieve full product details and all active retailer offers"
)
def get_product_detail(
    product_id: str,
    db: Session = Depends(get_db)
):
    """Get single product details with all competing retailer offers."""
    product = db.query(Product).filter(Product.id == product_id, Product.is_active == True).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or is currently inactive."
        )

    # Rank and explain all active offers
    ranked_offers = rank_and_explain_offers(product.offers)

    summary = _build_product_summary(product)
    return ProductDetailResponse(
        id=summary.id,
        title=summary.title,
        description=summary.description,
        category=summary.category,
        brand=summary.brand,
        image_url=summary.image_url,
        is_active=summary.is_active,
        is_demo_data=summary.is_demo_data,
        offer_count=len(ranked_offers),
        min_total_cost_paise=summary.min_total_cost_paise,
        min_total_cost_formatted=summary.min_total_cost_formatted,
        offers=ranked_offers
    )


@router.get(
    "/{product_id}/offers",
    response_model=List[RetailerOfferResponse],
    summary="Retrieve all offers for a product sorted by total cost"
)
def get_product_offers(
    product_id: str,
    sort_by: Optional[str] = Query("total_cost", description="Sort by: 'total_cost', 'price', 'delivery', 'rating'"),
    retailer: Optional[str] = Query(None, description="Filter by retailer name"),
    db: Session = Depends(get_db)
):
    """Retrieve all competing offers for a specific product.

    Ranked by confirmed landed cost (product price + shipping).
    Unconfirmed shipping offers are placed last.
    """
    product = db.query(Product).filter(Product.id == product_id, Product.is_active == True).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or is currently inactive."
        )

    offers = [o for o in product.offers if getattr(o, "is_active", True)]
    if retailer:
        offers = [o for o in offers if retailer.lower() in o.retailer_name.lower()]

    ranked = rank_and_explain_offers(offers)

    if sort_by == "price":
        ranked.sort(key=lambda o: o.product_price_paise)
    elif sort_by == "delivery":
        ranked.sort(key=lambda o: o.estimated_delivery_days)
    elif sort_by == "rating":
        ranked.sort(key=lambda o: -o.retailer_rating_tenth)

    return ranked
