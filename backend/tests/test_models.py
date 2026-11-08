"""Tests for database models, constraints, Argon2id security, and admin provisioning."""
import pytest
from sqlalchemy.exc import IntegrityError
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.models.product import Product, RetailerOffer
from app.models.order import Order, OrderItem
from app.scripts.create_admin import provision_admin


def test_user_creation_with_argon2id(db_session):
    """Verify User model stores an Argon2id hash and verifies correctly."""
    plain_password = "SecretUserPass123!"
    hashed = hash_password(plain_password)

    user = User(
        email="shopper@example.com",
        hashed_password=hashed,
        full_name="Alex Shopper",
        role="user",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert len(user.id) == 36  # UUID string
    assert user.role == "user"
    assert verify_password(plain_password, user.hashed_password) is True
    assert verify_password("WrongPassword123!", user.hashed_password) is False


def test_user_email_unique_constraint(db_session):
    """Verify that duplicate user emails violate the unique constraint."""
    user1 = User(
        email="duplicate@example.com",
        hashed_password=hash_password("Pass1"),
        full_name="User One",
        role="user"
    )
    db_session.add(user1)
    db_session.commit()

    user2 = User(
        email="duplicate@example.com",
        hashed_password=hash_password("Pass2"),
        full_name="User Two",
        role="user"
    )
    db_session.add(user2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_admin_provisioning_cli(db_session):
    """Verify admin provisioning script properly creates and elevates admin accounts."""
    # 1. Provision new admin
    result = provision_admin(
        email="superadmin@smartcart.local",
        password="AdminSecurePassword123!",
        full_name="Master Administrator",
        db=db_session
    )
    assert result is True

    admin = db_session.query(User).filter(User.email == "superadmin@smartcart.local").first()
    assert admin is not None
    assert admin.role == "admin"
    assert verify_password("AdminSecurePassword123!", admin.hashed_password) is True

    # 2. Provision existing user to elevate
    regular_user = User(
        email="promote_me@smartcart.local",
        hashed_password=hash_password("OldPassword123!"),
        full_name="Candidate User",
        role="user"
    )
    db_session.add(regular_user)
    db_session.commit()

    elevate_result = provision_admin(
        email="promote_me@smartcart.local",
        password="NewAdminPassword123!",
        full_name="Promoted User",
        db=db_session
    )
    assert elevate_result is True
    db_session.refresh(regular_user)
    assert regular_user.role == "admin"
    assert verify_password("NewAdminPassword123!", regular_user.hashed_password) is True


def test_product_and_retailer_offer_model(db_session):
    """Verify Product and RetailerOffer persistence, foreign keys, and integer paise storage."""
    product = Product(
        title="Test Noise Cancelling Headphones",
        description="Demo product for automated testing",
        category="Audio",
        brand="TestBrand",
        image_url="https://example.com/test.jpg",
        is_demo_data=True
    )
    db_session.add(product)
    db_session.flush()

    offer1 = RetailerOffer(
        product_id=product.id,
        retailer_name="Retailer Alpha (Demo)",
        product_price_paise=1999900,  # ₹19,999.00
        shipping_cost_paise=0,        # ₹0.00
        total_cost_paise=1999900,
        estimated_delivery_days=2,
        retailer_rating_tenth=48,     # 4.8 / 5.0
        review_count=520,
        return_policy="7 days returnable",
        stock_status="in_stock",
        is_demo_data=True
    )
    offer2 = RetailerOffer(
        product_id=product.id,
        retailer_name="Retailer Beta (Demo)",
        product_price_paise=1899900,  # ₹18,999.00
        shipping_cost_paise=50000,    # ₹500.00
        total_cost_paise=1949900,     # ₹19,499.00
        estimated_delivery_days=4,
        retailer_rating_tenth=42,     # 4.2 / 5.0
        review_count=130,
        return_policy="10 days returnable",
        stock_status="in_stock",
        is_demo_data=True
    )
    db_session.add_all([offer1, offer2])
    db_session.commit()

    # Query back and verify order_by total_cost_paise
    db_product = db_session.query(Product).filter(Product.id == product.id).first()
    assert db_product is not None
    assert len(db_product.offers) == 2
    assert db_product.is_demo_data is True

    # Retailer Beta has total 1949900 paise, which is cheaper than Alpha (1999900 paise)
    cheapest_offer = db_product.offers[0]
    assert cheapest_offer.retailer_name == "Retailer Beta (Demo)"
    assert cheapest_offer.total_cost_paise == 1949900
    assert cheapest_offer.rating_float == 4.2
    assert cheapest_offer.total_cost_formatted == "₹19,499.00"


def test_unique_product_retailer_constraint(db_session):
    """Enforce that a product cannot have duplicate offers from the same retailer."""
    product = Product(
        title="Test Mouse",
        category="Accessories",
        brand="Test",
        is_demo_data=True
    )
    db_session.add(product)
    db_session.flush()

    offer1 = RetailerOffer(
        product_id=product.id,
        retailer_name="SameStore",
        product_price_paise=100000,
        shipping_cost_paise=0,
        total_cost_paise=100000,
        is_demo_data=True
    )
    db_session.add(offer1)
    db_session.commit()

    # Add duplicate retailer for same product
    offer2 = RetailerOffer(
        product_id=product.id,
        retailer_name="SameStore",
        product_price_paise=95000,
        shipping_cost_paise=0,
        total_cost_paise=95000,
        is_demo_data=True
    )
    db_session.add(offer2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_order_and_order_item_lifecycle(db_session):
    """Verify Order creation with simulated notice and associated OrderItems."""
    user = User(
        email="buyer@example.com",
        hashed_password=hash_password("Pass1234"),
        full_name="Order Buyer",
        role="user"
    )
    product = Product(title="Test Keyboard", category="Accessories", brand="KeyBrand", is_demo_data=True)
    db_session.add_all([user, product])
    db_session.flush()

    offer = RetailerOffer(
        product_id=product.id,
        retailer_name="KeyStore",
        product_price_paise=499900,  # ₹4,999.00
        shipping_cost_paise=10000,   # ₹100.00
        total_cost_paise=509900,
        is_demo_data=True
    )
    db_session.add(offer)
    db_session.flush()

    order = Order(
        user_id=user.id,
        status="PENDING",
        total_paise=509900,
        currency="INR",
        idempotency_key="test-idem-key-001",
        paypal_order_id="TEST_PAYPAL_ORDER_123"
    )
    db_session.add(order)
    db_session.flush()

    order_item = OrderItem(
        order_id=order.id,
        offer_id=offer.id,
        quantity=1,
        unit_price_paise=499900,
        shipping_price_paise=10000,
        total_item_paise=509900
    )
    db_session.add(order_item)
    db_session.commit()

    # Query back
    saved_order = db_session.query(Order).filter(Order.id == order.id).first()
    assert saved_order is not None
    assert saved_order.status == "PENDING"
    assert saved_order.total_paise == 509900
    assert saved_order.total_formatted == "₹5,099.00"
    assert "simulated demo purchase" in saved_order.simulated_order_notice.lower()
    assert len(saved_order.items) == 1
    assert saved_order.items[0].unit_price_paise == 499900
