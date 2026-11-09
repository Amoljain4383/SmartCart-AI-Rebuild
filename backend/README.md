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
- **Phase 5: AI Shopping Copilot (`POST /api/copilot`)**:
  - Natural-language shopping inquiry interpretation powered optionally by Google Gemini (`gemini-3.8-flash`) via the `x-goog-api-key` header.
  - Automatic local deterministic fallback parser: seamlessly operates offline if `GEMINI_API_KEY` is omitted, invalid, or rate-limited.
  - Anti-hallucination boundary: AI strictly interprets user intent (search tokens, category, brand, budget cap). All product records, prices, shipping fees, and offer rankings are authoritatively retrieved and computed from the backend SQLite database.
  - In-memory sliding-window rate limiting (15 inquiries per minute per user or direct client IP).
  - Full demo transparency: all products, offers, and discounts are labeled as simulated demo data (`is_demo_data = True`).

---

## AI Shopping Copilot Configuration (`/api/copilot`)

### Enabling Gemini via `.env` (Optional)
Add your Google AI Studio API key to `backend/.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.8-flash
```
*Note: If omitted, the backend automatically uses the deterministic rule-based fallback parser with zero downtime and zero external dependencies.*

### Rate-Limiting Behavior
The Copilot enforces a maximum of **15 requests per minute** per client (keyed by authenticated `user.id` or guest socket IP via `request.client.host`). Exceeding this quota returns `HTTP 429 Too Many Requests`. This in-memory limiter resets upon server restart and is not shared across multi-worker deployments.

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
