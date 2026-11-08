"""Order and OrderItem models with idempotent payment tracking in integer paise."""
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import generate_uuid, TimestampMixin
from app.core.currency import paise_to_rupees_str


class Order(Base, TimestampMixin):
    """Order placed by a user for a simulated SmartCart purchase."""
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    status = Column(String(32), default="pending", nullable=False, index=True)
    # Valid Statuses: pending, paypal_created, paid, failed, cancelled

    total_paise = Column(Integer, nullable=False)
    currency = Column(String(8), default="INR", nullable=False)

    # PayPal transaction snapshot
    paypal_amount_str = Column(String(32), nullable=True)
    paypal_currency = Column(String(8), nullable=True)

    # Idempotency and Payment Recovery Keys
    idempotency_key = Column(String(64), unique=True, index=True, nullable=True)
    paypal_order_id = Column(String(64), unique=True, index=True, nullable=True)
    paypal_capture_id = Column(String(64), unique=True, index=True, nullable=True)

    shipping_address_json = Column(Text, nullable=True)
    simulated_order_notice = Column(
        String(255),
        default="SmartCart simulated demo purchase. No actual retailer order placed.",
        nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    @property
    def total_formatted(self) -> str:
        return paise_to_rupees_str(self.total_paise)

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, status='{self.status}', total_paise={self.total_paise})>"


class OrderItem(Base, TimestampMixin):
    """Individual item included in an order."""
    __tablename__ = "order_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    order_id = Column(
        String(36),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    offer_id = Column(
        String(36),
        ForeignKey("retailer_offers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    product_title_snapshot = Column(String(255), nullable=True)
    retailer_name_snapshot = Column(String(100), nullable=True)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price_paise = Column(Integer, nullable=False)
    shipping_price_paise = Column(Integer, default=0, nullable=False)
    total_item_paise = Column(Integer, nullable=False)

    # Relationships
    order = relationship("Order", back_populates="items")
    offer = relationship("RetailerOffer", back_populates="order_items")

    @property
    def unit_price_formatted(self) -> str:
        return paise_to_rupees_str(self.unit_price_paise)

    @property
    def shipping_price_formatted(self) -> str:
        return paise_to_rupees_str(self.shipping_price_paise)

    @property
    def total_item_formatted(self) -> str:
        return paise_to_rupees_str(self.total_item_paise)

    def __repr__(self) -> str:
        return (
            f"<OrderItem(id={self.id}, order_id={self.order_id}, "
            f"qty={self.quantity}, total_paise={self.total_item_paise})>"
        )
