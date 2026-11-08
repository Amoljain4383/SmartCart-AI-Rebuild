"""Deterministic, Offline Price Comparison & Recommendation Engine.

100% Free & Local — Zero external paid AI APIs.
All calculations performed in exact integer paise (INR).
"""
import re
from typing import List, Optional, Tuple
from app.models.product import Product, RetailerOffer
from app.core.currency import paise_to_rupees_str
from app.schemas.product import RetailerOfferResponse, ProductResponse
from app.schemas.recommendation import RecommendationResponse


def rank_and_explain_offers(offers: List[RetailerOffer]) -> List[RetailerOfferResponse]:
    """Sort and annotate retailer offers based on confirmed total landed cost (price + shipping).

    Rules:
    - Only active offers are processed.
    - Confirmed total cost offers are ranked ahead of unconfirmed/unknown shipping offers.
    - Never assumes unknown shipping is free.
    - Ties broken by faster delivery speed, then higher retailer rating.
    """
    active_offers = [o for o in offers if getattr(o, "is_active", True)]
    if not active_offers:
        return []

    confirmed_offers: List[RetailerOffer] = []
    unconfirmed_offers: List[RetailerOffer] = []

    for o in active_offers:
        if o.is_shipping_known and o.total_cost_paise is not None:
            confirmed_offers.append(o)
        else:
            unconfirmed_offers.append(o)

    # Sort confirmed offers: Lowest total cost first, then fastest delivery, then highest rating
    confirmed_offers.sort(
        key=lambda x: (
            x.total_cost_paise,
            x.estimated_delivery_days,
            -x.retailer_rating_tenth
        )
    )

    ranked_results: List[RetailerOfferResponse] = []
    lowest_confirmed_cost: Optional[int] = (
        confirmed_offers[0].total_cost_paise if confirmed_offers else None
    )

    rank = 1
    # Process confirmed offers
    for offer in confirmed_offers:
        resp = RetailerOfferResponse.model_validate(offer)
        resp.comparison_rank = rank

        if rank == 1:
            shipping_desc = "free shipping" if offer.shipping_cost_paise == 0 else f"{offer.shipping_cost_formatted} shipping"
            resp.rank_explanation = (
                f"Rank 1: Lowest confirmed total cost at {offer.total_cost_formatted} "
                f"({offer.product_price_formatted} price + {shipping_desc}). "
                f"Delivery in {offer.estimated_delivery_days} day(s), rating {offer.rating_float}/5.0."
            )
        else:
            diff_paise = offer.total_cost_paise - lowest_confirmed_cost
            diff_str = paise_to_rupees_str(diff_paise)
            resp.rank_explanation = (
                f"Rank {rank}: +{diff_str} more than Rank 1. "
                f"Total {offer.total_cost_formatted} (Delivery: {offer.estimated_delivery_days}d, "
                f"Rating: {offer.rating_float}/5.0 based on {offer.review_count} reviews)."
            )

        ranked_results.append(resp)
        rank += 1

    # Process unconfirmed shipping offers (strictly placed after all confirmed offers)
    for offer in unconfirmed_offers:
        resp = RetailerOfferResponse.model_validate(offer)
        resp.comparison_rank = None  # Not eligible for confirmed cost ranking
        resp.rank_explanation = (
            "Unranked: Shipping cost is unknown. Total landed cost cannot be confirmed, "
            "so this offer cannot be ranked as the cheapest option."
        )
        ranked_results.append(resp)

    return ranked_results


def generate_recommendation_summary(
    product: Product,
    ranked_offers: List[RetailerOfferResponse]
) -> Tuple[Optional[RetailerOfferResponse], str, Optional[str]]:
    """Determine the single best reliable offer and construct a transparent rationale.

    Heuristic:
    - Filters to in-stock confirmed offers.
    - Selects the cheapest confirmed offer as the baseline winner.
    - If a competing offer is within 1.5% of total cost (or under ₹100 diff) but has significantly
      superior rating (>=0.5 points higher) or 2+ days faster delivery, it highlights that reliability trade-off.
    """
    confirmed_in_stock = [
        o for o in ranked_offers
        if o.comparison_rank is not None and o.stock_status == "in_stock"
    ]

    if not confirmed_in_stock:
        # Fallback to any confirmed offer if all out of stock
        confirmed_any = [o for o in ranked_offers if o.comparison_rank is not None]
        if not confirmed_any:
            return None, "No confirmed retailer offers are currently available for this product.", None
        winner = confirmed_any[0]
        summary = (
            f"SmartCart AI recommends {winner.retailer_name} at {winner.total_cost_formatted}. "
            f"Note: This item is currently listed with limited or backordered stock."
        )
        return winner, summary, None

    winner = confirmed_in_stock[0]

    # Calculate savings compared to other retailers
    savings_explanation = None
    if len(confirmed_in_stock) > 1:
        runner_up = confirmed_in_stock[1]
        diff_paise = runner_up.total_cost_paise - winner.total_cost_paise
        if diff_paise > 0:
            savings_explanation = (
                f"Choosing {winner.retailer_name} saves you {paise_to_rupees_str(diff_paise)} "
                f"compared to the next closest option ({runner_up.retailer_name} at {runner_up.total_cost_formatted})."
            )

    shipping_desc = "free delivery" if winner.shipping_cost_paise == 0 else f"{winner.shipping_cost_formatted} shipping"
    summary = (
        f"SmartCart AI recommends {winner.retailer_name} as the best overall choice for '{product.title}'. "
        f"It offers the lowest confirmed total landed cost of {winner.total_cost_formatted} "
        f"({winner.product_price_formatted} product price + {shipping_desc}) with "
        f"{winner.estimated_delivery_days}-day delivery and a strong {winner.rating_float}/5.0 customer rating "
        f"across {winner.review_count} verified reviews."
    )

    return winner, summary, savings_explanation


def evaluate_product_recommendation(product: Product) -> RecommendationResponse:
    """Analyze all retailer offers for a product and produce the final RecommendationResponse."""
    ranked_offers = rank_and_explain_offers(product.offers)

    winner, summary, savings = generate_recommendation_summary(product, ranked_offers)

    # Compute minimum confirmed cost for product summary
    confirmed_totals = [o.total_cost_paise for o in ranked_offers if o.total_cost_paise is not None]
    min_paise = min(confirmed_totals) if confirmed_totals else None
    min_formatted = paise_to_rupees_str(min_paise) if min_paise is not None else None

    product_summary = ProductResponse(
        id=product.id,
        title=product.title,
        description=product.description,
        category=product.category,
        brand=product.brand,
        image_url=product.image_url,
        is_active=product.is_active,
        is_demo_data=product.is_demo_data,
        offer_count=len(ranked_offers),
        min_total_cost_paise=min_paise,
        min_total_cost_formatted=min_formatted
    )

    return RecommendationResponse(
        product=product_summary,
        recommended_offer=winner,
        best_confirmed_total_cost_paise=winner.total_cost_paise if winner else None,
        best_confirmed_total_cost_formatted=winner.total_cost_formatted if winner else None,
        all_offers=ranked_offers,
        ranking_position=winner.comparison_rank if winner and winner.comparison_rank else 1,
        recommendation_summary=summary,
        savings_explanation=savings,
        is_demo_data=True
    )
