"""Demo Catalogue Seeding Script.

Populates realistic simulated products and multi-retailer offers.
ALL records are explicitly tagged with `is_demo_data = True`.
ALL monetary values are stored in integer paise (INR).
"""
import sys
from typing import List, Dict, Any
from app.core.database import SessionLocal
from app.core.currency import compute_landed_cost_paise, rupees_to_paise
from app.models.product import Product, RetailerOffer

# Realistic Simulated Demo Catalog (All values explicitly marked simulated demo)
DEMO_PRODUCTS: List[Dict[str, Any]] = [
    {
        "title": "Sony WH-1000XM5 Wireless Noise Cancelling Headphones",
        "description": "Simulated Demo: Industry-leading noise cancellation with two processors and 8 microphones. Up to 30-hour battery life.",
        "category": "Audio",
        "brand": "Sony",
        "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&auto=format&fit=crop&q=60",
        "offers": [
            {
                "retailer_name": "ElectroMart India (Demo)",
                "retailer_logo_url": "https://placehold.co/120x40/png?text=ElectroMart",
                "product_price_inr": "26990.00",
                "shipping_cost_inr": "0.00",
                "estimated_delivery_days": 2,
                "rating_tenth": 47,  # 4.7 / 5.0
                "review_count": 840,
                "return_policy": "7 days replacement",
                "stock_status": "in_stock",
            },
            {
                "retailer_name": "SonicSound Store (Demo)",
                "retailer_logo_url": "https://placehold.co/120x40/png?text=SonicSound",
                "product_price_inr": "25999.00",
                "shipping_cost_inr": "499.00",
                "estimated_delivery_days": 4,
                "rating_tenth": 44,  # 4.4 / 5.0
                "review_count": 310,
                "return_policy": "10 days returnable",
                "stock_status": "in_stock",
            },
            {
                "retailer_name": "GadgetWorld (Simulated)",
                "retailer_logo_url": "https://placehold.co/120x40/png?text=GadgetWorld",
                "product_price_inr": "27499.00",
                "shipping_cost_inr": "0.00",
                "estimated_delivery_days": 1,
                "rating_tenth": 48,  # 4.8 / 5.0
                "review_count": 1250,
                "return_policy": "15 days replacement",
                "stock_status": "in_stock",
            },
        ],
    },
    {
        "title": "Apple Watch Series 9 GPS 45mm",
        "description": "Simulated Demo: Advanced health tracking, S9 chip, bright always-on Retina display, and double tap gesture.",
        "category": "Wearables",
        "brand": "Apple",
        "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&auto=format&fit=crop&q=60",
        "offers": [
            {
                "retailer_name": "iStore Direct (Demo)",
                "retailer_logo_url": "https://placehold.co/120x40/png?text=iStore",
                "product_price_inr": "41900.00",
                "shipping_cost_inr": "0.00",
                "estimated_delivery_days": 2,
                "rating_tenth": 49,
                "review_count": 1420,
                "return_policy": "14 days Apple warranty",
                "stock_status": "in_stock",
            },
            {
                "retailer_name": "QuickCart Express (Simulated)",
                "retailer_logo_url": "https://placehold.co/120x40/png?text=QuickCart",
                "product_price_inr": "39999.00",
                "shipping_cost_inr": "750.00",
                "estimated_delivery_days": 3,
                "rating_tenth": 43,
                "review_count": 215,
                "return_policy": "7 days returnable",
                "stock_status": "in_stock",
            },
            {
                "retailer_name": "Metro Retailers (Demo)",
                "retailer_logo_url": "https://placehold.co/120x40/png?text=Metro",
                "product_price_inr": "42500.00",
                "shipping_cost_inr": "0.00",
                "estimated_delivery_days": 1,
                "rating_tenth": 46,
                "review_count": 590,
                "return_policy": "10 days returnable",
                "stock_status": "in_stock",
            },
        ],
    },
    {
        "title": "Logitech MX Master 3S Wireless Mouse",
        "description": "Simulated Demo: Quiet clicks, 8K DPI any-surface tracking, MagSpeed electromagnetic scrolling, ergonomic design.",
        "category": "Accessories",
        "brand": "Logitech",
        "image_url": "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=600&auto=format&fit=crop&q=60",
        "offers": [
            {
                "retailer_name": "OfficeGizmos (Demo)",
                "retailer_logo_url": "https://placehold.co/120x40/png?text=OfficeGizmos",
                "product_price_inr": "8495.00",
                "shipping_cost_inr": "150.00",
                "estimated_delivery_days": 3,
                "rating_tenth": 45,
                "review_count": 480,
                "return_policy": "7 days replacement",
                "stock_status": "in_stock",
            },
            {
                "retailer_name": "TechHub India (Simulated)",
                "retailer_logo_url": "https://placehold.co/120x40/png?text=TechHub",
                "product_price_inr": "8299.00",
                "shipping_cost_inr": "200.00",
                "estimated_delivery_days": 4,
                "rating_tenth": 46,
                "review_count": 670,
                "return_policy": "10 days replacement",
                "stock_status": "in_stock",
            },
            {
                "retailer_name": "PrimeDirect Electronics (Demo)",
                "retailer_logo_url": "https://placehold.co/120x40/png?text=PrimeDirect",
                "product_price_inr": "8799.00",
                "shipping_cost_inr": "0.00",
                "estimated_delivery_days": 1,
                "rating_tenth": 49,
                "review_count": 1890,
                "return_policy": "15 days returnable",
                "stock_status": "in_stock",
            },
        ],
    },
    {
        "title": "Kindle Paperwhite (16 GB) 6.8 inch Display",
        "description": "Simulated Demo: Adjustable warm light, up to 10 weeks of battery life, 20% faster page turns, waterproof.",
        "category": "Electronics",
        "brand": "Amazon",
        "image_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600&auto=format&fit=crop&q=60",
        "offers": [
            {
                "retailer_name": "BookWorm India (Demo)",
                "retailer_logo_url": "https://placehold.co/120x40/png?text=BookWorm",
                "product_price_inr": "13999.00",
                "shipping_cost_inr": "0.00",
                "estimated_delivery_days": 2,
                "rating_tenth": 48,
                "review_count": 1100,
                "return_policy": "10 days returnable",
                "stock_status": "in_stock",
            },
            {
                "retailer_name": "DigitalReading Hub (Simulated)",
                "retailer_logo_url": "https://placehold.co/120x40/png?text=DigitalReading",
                "product_price_inr": "13499.00",
                "shipping_cost_inr": "350.00",
                "estimated_delivery_days": 5,
                "rating_tenth": 42,
                "review_count": 160,
                "return_policy": "7 days returnable",
                "stock_status": "in_stock",
            },
        ],
    },
    {
        "title": "Dyson V8 Absolute Cordless Vacuum Cleaner",
        "description": "Simulated Demo: Powerful cordless cleaning with de-tangling technology. Up to 40 minutes run time.",
        "category": "Home Appliances",
        "brand": "Dyson",
        "image_url": "https://images.unsplash.com/photo-1558317374-067fb5f30001?w=600&auto=format&fit=crop&q=60",
        "offers": [
            {
                "retailer_name": "HomeAppliance Center (Demo)",
                "retailer_logo_url": "https://placehold.co/120x40/png?text=HomeAppliance",
                "product_price_inr": "32900.00",
                "shipping_cost_inr": "0.00",
                "estimated_delivery_days": 2,
                "rating_tenth": 47,
                "review_count": 520,
                "return_policy": "10 days replacement",
                "stock_status": "in_stock",
            },
            {
                "retailer_name": "ElectroSuperstore (Simulated)",
                "retailer_logo_url": "https://placehold.co/120x40/png?text=ElectroSuper",
                "product_price_inr": "31500.00",
                "shipping_cost_inr": "999.00",
                "estimated_delivery_days": 4,
                "rating_tenth": 44,
                "review_count": 280,
                "return_policy": "7 days returnable",
                "stock_status": "in_stock",
            },
            {
                "retailer_name": "Dyson Direct Authorized (Demo)",
                "retailer_logo_url": "https://placehold.co/120x40/png?text=DysonDirect",
                "product_price_inr": "33900.00",
                "shipping_cost_inr": "0.00",
                "estimated_delivery_days": 1,
                "rating_tenth": 49,
                "review_count": 940,
                "return_policy": "15 days replacement",
                "stock_status": "in_stock",
            },
        ],
    },
]


def seed_demo_catalog(force_reset: bool = False) -> None:
    """Seed the database with realistic demo catalogue data in integer paise."""
    db = SessionLocal()
    try:
        existing_count = db.query(Product).count()
        if existing_count > 0 and not force_reset:
            print(f"[INFO] Catalog already contains {existing_count} products. Skipping seeding.")
            return

        if force_reset and existing_count > 0:
            print("[INFO] Resetting existing demo catalogue...")
            db.query(RetailerOffer).delete()
            db.query(Product).delete()
            db.commit()

        print("Seeding realistic demo products & retailer offers...")
        total_offers_count = 0

        for item in DEMO_PRODUCTS:
            product = Product(
                title=item["title"],
                description=item["description"],
                category=item["category"],
                brand=item["brand"],
                image_url=item["image_url"],
                is_active=True,
                is_demo_data=True,  # Explicitly flagged
            )
            db.add(product)
            db.flush()  # Generates product.id

            for off in item["offers"]:
                price_paise = rupees_to_paise(off["product_price_inr"])
                shipping_paise = rupees_to_paise(off["shipping_cost_inr"])
                total_paise = compute_landed_cost_paise(price_paise, shipping_paise)

                offer = RetailerOffer(
                    product_id=product.id,
                    retailer_name=off["retailer_name"],
                    retailer_logo_url=off["retailer_logo_url"],
                    product_price_paise=price_paise,
                    shipping_cost_paise=shipping_paise,
                    is_shipping_known=True,
                    total_cost_paise=total_paise,
                    estimated_delivery_days=off["estimated_delivery_days"],
                    retailer_rating_tenth=off["rating_tenth"],
                    review_count=off["review_count"],
                    return_policy=off["return_policy"],
                    stock_status=off["stock_status"],
                    offer_url=f"https://example.com/demo-retailer/{product.id}",
                    is_active=True,
                    is_demo_data=True,  # Explicitly flagged
                )
                db.add(offer)
                total_offers_count += 1

        db.commit()
        print(f"[SUCCESS] Seeded {len(DEMO_PRODUCTS)} demo products and {total_offers_count} simulated offers.")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to seed demo catalog: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    force = "--reset" in sys.argv
    seed_demo_catalog(force_reset=force)
