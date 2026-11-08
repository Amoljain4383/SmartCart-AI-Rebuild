"""Recommendation API Router powered by the deterministic offline engine."""
import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.product import Product
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
from app.services.recommendation_engine import evaluate_product_recommendation

router = APIRouter(prefix="", tags=["Recommendations"])


@router.post(
    "",
    response_model=RecommendationResponse,
    summary="Compute cheapest reliable offer recommendation for a product"
)
def get_recommendation(
    request: RecommendationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Recommend the cheapest reliable offer for a product.

    Requires an authenticated user session.
    Operates 100% offline via deterministic rule-based algorithms (Zero external AI token costs).
    """
    target_product = None

    if request.product_id:
        target_product = (
            db.query(Product)
            .filter(Product.id == request.product_id.strip(), Product.is_active == True)
            .first()
        )
        if not target_product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id '{request.product_id}' not found or is inactive."
            )

    elif request.query and request.query.strip():
        query_text = request.query.strip()
        tokens = [t.lower() for t in re.split(r"\s+", query_text) if len(t) > 0]
        active_products = db.query(Product).filter(Product.is_active == True).all()

        for prod in active_products:
            haystack = f"{prod.title} {prod.brand} {prod.category} {prod.description or ''}".lower()
            if all(t in haystack for t in tokens):
                target_product = prod
                break

        if not target_product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active products matching query '{request.query}' were found in the catalog."
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'product_id' or a non-empty 'query' string must be provided."
        )

    recommendation = evaluate_product_recommendation(target_product)
    return recommendation
