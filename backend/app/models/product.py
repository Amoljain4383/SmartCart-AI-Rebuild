"""Product and RetailerOffer models with integer paise monetary fields."""
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import generate_uuid, TimestampMixin
from app.core.currency import paise_to_rupees_str, paise_to_decimal


class Product(Base, TimestampMixin):
    """Product catalog item."""
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), index=True, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), index=True, nullable=False)
    brand = Column(String(100), index=True, nullable=False)
    image_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_demo_data = Column(Boolean, default=True, nullable=False)

    # Relationships
    offers = relationship(
        "RetailerOffer",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="RetailerOffer.total_cost_paise"
    )

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, title='{self.title}', category='{self.category}')>"


class RetailerOffer(Base, TimestampMixin):
    """An offer for a product from a specific retailer."""
    __tablename__ = "retailer_offers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    product_id = Column(
        String(36),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    retailer_name = Column(String(100), index=True, nullable=False)
    retailer_logo_url = Column(String(500), nullable=True)

    # Monetary values in integer paise
    product_price_paise = Column(Integer, nullable=False)
    shipping_cost_paise = Column(Integer, default=0, nullable=True)
    is_shipping_known = Column(Boolean, default=True, nullable=False)
    total_cost_paise = Column(Integer, index=True, nullable=True)

    # Shipping and reputation metrics
    estimated_delivery_days = Column(Integer, default=3, nullable=False)
    retailer_rating_tenth = Column(Integer, default=45, nullable=False)  # 45 = 4.5/5.0
    review_count = Column(Integer, default=0, nullable=False)
    return_policy = Column(String(100), default="14 days returnable", nullable=False)
    stock_status = Column(String(32), default="in_stock", nullable=False)  # "in_stock", "out_of_stock"
    offer_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_demo_data = Column(Boolean, default=True, nullable=False)

    # Relationships
    product = relationship("Product", back_populates="offers")
    order_items = relationship("OrderItem", back_populates="offer")

    # Enforce only one offer per retailer per product
    __table_args__ = (
        UniqueConstraint("product_id", "retailer_name", name="uq_product_retailer"),
    )

    @property
    def rating_float(self) -> float:
        """Helper to expose rating out of 5.0 for display."""
        return round(self.retailer_rating_tenth / 10.0, 1)

    @property
    def is_total_confirmed(self) -> bool:
        return self.is_shipping_known and (self.total_cost_paise is not None)

    @property
    def product_price_formatted(self) -> str:
        return paise_to_rupees_str(self.product_price_paise)

    @property
    def shipping_cost_formatted(self) -> str:
        if not self.is_shipping_known or self.shipping_cost_paise is None:
            return "Unknown / Unconfirmed"
        return paise_to_rupees_str(self.shipping_cost_paise)

    @property
    def total_cost_formatted(self) -> str:
        if not self.is_total_confirmed or self.total_cost_paise is None:
            return "Incomplete (Unknown Shipping)"
        return paise_to_rupees_str(self.total_cost_paise)

    def __repr__(self) -> str:
        return (
            f"<RetailerOffer(id={self.id}, retailer='{self.retailer_name}', "
            f"total_paise={self.total_cost_paise})>"
        )
