# SmartCart AI — Backend Service

FastAPI-powered backend for SmartCart AI, offering product comparison, rule-based recommendation logic, and PayPal Sandbox payments.

---

## Features Implemented So Far

- **Phase 1: Foundation & Financial Models**:
  - Exact financial calculations in **integer paise** (INR). No floating-point rounding errors.
  - SQLAlchemy models supporting both local SQLite and production Neon PostgreSQL.
  - Idempotent schema initialization and demo catalog seeding (`is_demo_data = True`).
  - Out-of-band Admin provisioning CLI.
- **Phase 2: Authentication & Admin Security**:
  - **Argon2id** password hashing (`argon2-cffi`).
  - **JWT Bearer Token** authentication with configurable expiry and secret keys.
  - Role-Based Access Control (`user` vs `admin`).
  - Protected admin routes with strict HTTP 401 / 403 handling.
  - Public registration hardcoded strictly to `role = "user"`.
  - Token Denylist (`RevokedToken` table with `jti`) for genuine server-side JWT revocation on logout.
  - Zero password hashes exposed in responses.
- **Phase 3: Product Catalogue, Price Comparison & Recommendation Engine**:
  - Full product search avoiding false-positive model collisions (e.g. Series 9 vs Series 8, XM5 vs XM4).
  - Multi-retailer offer comparison sorting by confirmed total landed cost (`Product price + Shipping`).
  - Unknown shipping protection: offers with unknown shipping are never ranked as the cheapest confirmed option.
  - 100% Free, offline deterministic Intelligent Recommendation Engine (`POST /api/recommendations`).
  - Admin catalogue controls: create/update products & offers, activate/deactivate status with RBAC enforcement.
- **Phase 4: PayPal Sandbox Integration & Order Management**:
  - Server-calculated integer paise order totals (client-submitted prices are strictly ignored).
  - Server-side PayPal Sandbox order creation and verification (`/v2/checkout/orders`).
  - Idempotent capture protection and server-side amount & currency verification.
  - Safe handling of network timeouts and missing credentials (HTTP 503/504).
  - User order history and receipt details isolated strictly by user ownership.
  - Comprehensive documentation in [PAYPAL_INTEGRATION.md](docs/PAYPAL_INTEGRATION.md).

---

## Quickstart

### 1. Environment Setup
```powershell
# From project root:
cd backend
..\.venv\Scripts\python.exe -m app.db.init_db
..\.venv\Scripts\python.exe -m app.scripts.seed_demo_catalog
```

### 2. Run the Development Server
```powershell
..\.venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000
```
- API root: `http://127.0.0.1:8000/`
- Interactive Swagger UI: `http://127.0.0.1:8000/docs`

### 3. Run Tests
```powershell
..\.venv\Scripts\pytest.exe -v
```

For complete authentication details, see [AUTHENTICATION.md](docs/AUTHENTICATION.md).
