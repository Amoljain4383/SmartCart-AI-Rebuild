"""FastAPI Application Entry Point for SmartCart AI."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.db.init_db import init_db
from app.api.auth import router as auth_router
from app.api.admin import router as admin_router
from app.api.products import router as products_router
from app.api.recommendations import router as recommendations_router
from app.api.orders import router as orders_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize database tables on startup."""
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="SmartCart AI Backend — Product Comparison & Recommendation Engine (Simulated Demo)",
    version="0.1.0",
    lifespan=lifespan
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router, prefix="/api/auth")
app.include_router(admin_router, prefix="/api/admin")
app.include_router(products_router, prefix="/api/products")
app.include_router(recommendations_router, prefix="/api/recommendations")
app.include_router(orders_router, prefix="/api/orders")

# v1 Aliases for versioning
app.include_router(auth_router, prefix="/api/v1/auth", include_in_schema=False)
app.include_router(admin_router, prefix="/api/v1/admin", include_in_schema=False)
app.include_router(products_router, prefix="/api/v1/products", include_in_schema=False)
app.include_router(recommendations_router, prefix="/api/v1/recommendations", include_in_schema=False)
app.include_router(orders_router, prefix="/api/v1/orders", include_in_schema=False)


@app.get("/", tags=["Health"])
def root_status():
    """Root endpoint confirming API status and demo mode."""
    return {
        "app": settings.APP_NAME,
        "status": "online",
        "version": "0.1.0",
        "currency": settings.CURRENCY,
        "monetary_unit": "Integer Paise (1 INR = 100 paise)",
        "demo_mode": True,
        "notice": "All product prices, shipping rates, and retailer offers are simulated demo data."
    }


@app.get("/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint verifying database connectivity."""
    db.execute(text("SELECT 1"))
    return {
        "status": "healthy",
        "database": "connected",
        "environment": settings.ENVIRONMENT
    }
