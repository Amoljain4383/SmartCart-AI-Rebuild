"""Protected administrative routes with RBAC enforcement and catalogue management."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_admin_user
from app.models.user import User
from app.models.product import Product, RetailerOffer
from app.schemas.auth import AdminDashboardResponse, MessageResponse
from app.schemas.product import (
    ProductResponse,
    ProductDetailResponse,
    ProductCreateRequest,
    ProductUpdateRequest,
    RetailerOfferResponse,
    OfferCreateRequest,
    OfferUpdateRequest,
)
from app.core.currency import rupees_to_paise, compute_landed_cost_paise, paise_to_rupees_str
from app.services.recommendation_engine import rank_and_explain_offers

router = APIRouter(prefix="", tags=["Admin"])


@router.get(
    "/dashboard",
    response_model=AdminDashboardResponse,
    summary="Access protected admin dashboard"
)
def admin_dashboard(
    current_admin: User = Depends(get_current_admin_user)
):
    """Protected admin dashboard endpoint.

    Accessible strictly by authenticated accounts with role='admin'.
    Standard users receive HTTP 403 Forbidden.
    Unauthenticated users receive HTTP 401 Unauthorized.
    """
    return AdminDashboardResponse(
        status="success",
        message="Admin dashboard access granted.",
        admin={
            "id": current_admin.id,
            "email": current_admin.email,
            "full_name": current_admin.full_name,
            "role": current_admin.role,
        }
    )


# -----------------------------------------------------------------------------
# Admin Product Management
# -----------------------------------------------------------------------------

@router.post(
    "/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Admin: Create a new product in the catalog"
)
def admin_create_product(
    request: ProductCreateRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new product. Strictly requires admin privileges."""
    new_product = Product(
        title=request.title.strip(),
        description=request.description.strip() if request.description else None,
        category=request.category.strip(),
        brand=request.brand.strip(),
        image_url=request.image_url.strip() if request.image_url else None,
        is_active=request.is_active,
        is_demo_data=True
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return ProductResponse(
        id=new_product.id,
        title=new_product.title,
        description=new_product.description,
        category=new_product.category,
        brand=new_product.brand,
        image_url=new_product.image_url,
        is_active=new_product.is_active,
        is_demo_data=new_product.is_demo_data,
        offer_count=0,
        min_total_cost_paise=None,
        min_total_cost_formatted=None
    )


@router.put(
    "/products/{product_id}",
    response_model=ProductResponse,
    summary="Admin: Update product details"
)
def admin_update_product(
    product_id: str,
    request: ProductUpdateRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update existing product details. Strictly requires admin privileges."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id '{product_id}' not found."
        )

    if request.title is not None:
        product.title = request.title.strip()
    if request.description is not None:
        product.description = request.description.strip() if request.description else None
    if request.category is not None:
        product.category = request.category.strip()
    if request.brand is not None:
        product.brand = request.brand.strip()
    if request.image_url is not None:
        product.image_url = request.image_url.strip() if request.image_url else None
    if request.is_active is not None:
        product.is_active = request.is_active

    db.commit()
    db.refresh(product)

    active_offers = [o for o in product.offers if o.is_active and o.is_shipping_known and o.total_cost_paise is not None]
    min_paise = min((o.total_cost_paise for o in active_offers), default=None)

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
        min_total_cost_formatted=paise_to_rupees_str(min_paise) if min_paise else None
    )


@router.patch(
    "/products/{product_id}/status",
    response_model=ProductResponse,
    summary="Admin: Activate or deactivate a product"
)
def admin_toggle_product_status(
    product_id: str,
    is_active: bool,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Activate or deactivate a product from public catalog visibility."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id '{product_id}' not found."
        )
    product.is_active = is_active
    db.commit()
    db.refresh(product)

    return ProductResponse(
        id=product.id,
        title=product.title,
        description=product.description,
        category=product.category,
        brand=product.brand,
        image_url=product.image_url,
        is_active=product.is_active,
        is_demo_data=product.is_demo_data,
        offer_count=len(product.offers)
    )


# -----------------------------------------------------------------------------
# Admin Offer Management
# -----------------------------------------------------------------------------

@router.post(
    "/products/{product_id}/offers",
    response_model=RetailerOfferResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Admin: Create a retailer offer for a product"
)
def admin_create_offer(
    product_id: str,
    request: OfferCreateRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Add a new retailer offer to a product in integer paise."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id '{product_id}' not found."
        )

    # Convert money to integer paise
    try:
        price_paise = rupees_to_paise(request.product_price)
        if price_paise < 0:
            raise ValueError("Price cannot be negative")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid product price: {e}")

    shipping_paise = None
    if request.is_shipping_known and request.shipping_cost is not None:
        try:
            shipping_paise = rupees_to_paise(request.shipping_cost)
            if shipping_paise < 0:
                raise ValueError("Shipping cost cannot be negative")
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid shipping cost: {e}")
    elif not request.is_shipping_known:
        shipping_paise = None

    total_paise = compute_landed_cost_paise(price_paise, shipping_paise)

    # Check unique retailer constraint
    existing = db.query(RetailerOffer).filter(
        RetailerOffer.product_id == product_id,
        RetailerOffer.retailer_name == request.retailer_name.strip()
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An offer from retailer '{request.retailer_name}' already exists for this product."
        )

    new_offer = RetailerOffer(
        product_id=product_id,
        retailer_name=request.retailer_name.strip(),
        retailer_logo_url=request.retailer_logo_url.strip() if request.retailer_logo_url else None,
        product_price_paise=price_paise,
        shipping_cost_paise=shipping_paise,
        is_shipping_known=request.is_shipping_known,
        total_cost_paise=total_paise,
        estimated_delivery_days=request.estimated_delivery_days,
        retailer_rating_tenth=request.retailer_rating_tenth,
        review_count=request.review_count,
        return_policy=request.return_policy,
        stock_status=request.stock_status,
        offer_url=request.offer_url,
        is_active=request.is_active,
        is_demo_data=True
    )
    db.add(new_offer)
    db.commit()
    db.refresh(new_offer)

    return RetailerOfferResponse.model_validate(new_offer)


@router.put(
    "/offers/{offer_id}",
    response_model=RetailerOfferResponse,
    summary="Admin: Update an existing retailer offer"
)
def admin_update_offer(
    offer_id: str,
    request: OfferUpdateRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update existing retailer offer pricing, shipping, or stock."""
    offer = db.query(RetailerOffer).filter(RetailerOffer.id == offer_id).first()
    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Retailer offer with id '{offer_id}' not found."
        )

    if request.retailer_name is not None:
        offer.retailer_name = request.retailer_name.strip()
    if request.retailer_logo_url is not None:
        offer.retailer_logo_url = request.retailer_logo_url.strip() if request.retailer_logo_url else None

    # Update pricing if supplied
    if request.product_price is not None:
        price_paise = rupees_to_paise(request.product_price)
        if price_paise < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product price cannot be negative")
        offer.product_price_paise = price_paise

    if request.is_shipping_known is not None:
        offer.is_shipping_known = request.is_shipping_known

    if request.shipping_cost is not None:
        shipping_paise = rupees_to_paise(request.shipping_cost)
        if shipping_paise < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Shipping cost cannot be negative")
        offer.shipping_cost_paise = shipping_paise
        offer.is_shipping_known = True
    elif request.is_shipping_known is False:
        offer.shipping_cost_paise = None

    # Recompute landed cost
    offer.total_cost_paise = compute_landed_cost_paise(
        offer.product_price_paise,
        offer.shipping_cost_paise if offer.is_shipping_known else None
    )

    if request.estimated_delivery_days is not None:
        offer.estimated_delivery_days = request.estimated_delivery_days
    if request.retailer_rating_tenth is not None:
        offer.retailer_rating_tenth = request.retailer_rating_tenth
    if request.review_count is not None:
        offer.review_count = request.review_count
    if request.return_policy is not None:
        offer.return_policy = request.return_policy
    if request.stock_status is not None:
        offer.stock_status = request.stock_status
    if request.offer_url is not None:
        offer.offer_url = request.offer_url
    if request.is_active is not None:
        offer.is_active = request.is_active

    db.commit()
    db.refresh(offer)

    return RetailerOfferResponse.model_validate(offer)


@router.patch(
    "/offers/{offer_id}/status",
    response_model=RetailerOfferResponse,
    summary="Admin: Activate or deactivate a retailer offer"
)
def admin_toggle_offer_status(
    offer_id: str,
    is_active: bool,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Activate or deactivate a retailer offer."""
    offer = db.query(RetailerOffer).filter(RetailerOffer.id == offer_id).first()
    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Retailer offer with id '{offer_id}' not found."
        )
    offer.is_active = is_active
    db.commit()
    db.refresh(offer)

    return RetailerOfferResponse.model_validate(offer)
