"""Database schema initialization and lightweight migration.

Creates tables for all models registered in Base metadata if they do not exist.
Safe for SQLite and PostgreSQL.
"""
import sys
from sqlalchemy import inspect, text
from app.core.database import engine, Base
import app.models  # Ensures all models are imported and registered with Base metadata


def _migrate_columns():
    """Ensure newly introduced columns are added to existing SQLite/Postgres tables."""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        if "products" in tables:
            columns = [c["name"] for c in inspector.get_columns("products")]
            if "is_active" not in columns:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE products ADD COLUMN is_active BOOLEAN DEFAULT 1"))
                    conn.commit()

        if "retailer_offers" in tables:
            columns = [c["name"] for c in inspector.get_columns("retailer_offers")]
            if "is_active" not in columns:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE retailer_offers ADD COLUMN is_active BOOLEAN DEFAULT 1"))
                    conn.commit()
            if "is_shipping_known" not in columns:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE retailer_offers ADD COLUMN is_shipping_known BOOLEAN DEFAULT 1"))
                    conn.commit()

        if "orders" in tables:
            columns = [c["name"] for c in inspector.get_columns("orders")]
            if "paypal_amount_str" not in columns:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE orders ADD COLUMN paypal_amount_str VARCHAR(32)"))
                    conn.commit()
            if "paypal_currency" not in columns:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE orders ADD COLUMN paypal_currency VARCHAR(8)"))
                    conn.commit()

        if "order_items" in tables:
            columns = [c["name"] for c in inspector.get_columns("order_items")]
            if "product_title_snapshot" not in columns:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE order_items ADD COLUMN product_title_snapshot VARCHAR(255)"))
                    conn.commit()
            if "retailer_name_snapshot" not in columns:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE order_items ADD COLUMN retailer_name_snapshot VARCHAR(100)"))
                    conn.commit()
    except Exception as e:
        print(f"[WARNING] Migration check encountered: {e}")


def init_db() -> None:
    """Create all database tables and perform column migrations."""
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    _migrate_columns()
    print("Database tables created successfully.")


if __name__ == "__main__":
    init_db()
