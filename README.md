# SmartCart AI — AI Shopping Copilot & True Landed Cost Engine

> **PayPal AI Hackathon Submission**
> Transparent e-commerce intelligence: Eliminating deceptive sticker prices through automated landed-cost auditing and AI-driven shopping intent extraction.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React 18](https://img.shields.io/badge/React-18.3-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-5.4-646CFF.svg?logo=vite&logoColor=white)](https://vitejs.dev)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![PayPal Sandbox](https://img.shields.io/badge/PayPal-Sandbox_SDK-00457C.svg?logo=paypal&logoColor=white)](https://developer.paypal.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg?logo=python&logoColor=white)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 1. Project Overview & Problem Statement

### The Problem: Deceptive Sticker Prices & Comparison Fatigue
In modern online shopping, consumers are frequently misled by surface sticker prices. A marketplace offer might advertise headphones at ₹24,999, but sneakily tack on ₹1,200 shipping, ₹300 handling, or restrictive return penalties at the final checkout step. Conversely, an offer listed at ₹25,499 with free delivery and trusted seller ratings is actually the cheaper and safer purchase.

Moreover, traditional keyword search forces shoppers to manually filter through dozens of irrelevant specs, compare complex shipping policies across retailers, and perform mental arithmetic to calculate true totals.

### The Solution: SmartCart AI
**SmartCart AI** solves this with a two-pillar architecture:
1. **AI Shopping Copilot**: Accepts plain-English natural language requests (e.g., *"I need Sony noise-cancelling headphones under ₹28,000 for college"*), extracts structured search intent (category, brand, budget cap, key features), and matches verified catalogue products.
2. **True Landed Cost Engine**: Audits every competing multi-retailer offer by adding base price and verified delivery fees calculated authoritatively on the backend using integer paise ($1\text{ INR} = 100\text{ paise}$). Offers with hidden fees lose top ranking, and offers with unconfirmed shipping are strictly quarantined.

---

## 2. Main Features

- 💬 **Natural Language AI Shopping Copilot**: Describe your shopping requirements in conversational English; the Copilot extracts criteria, parses budget limits, and highlights key features.
- ⚡ **Dual AI & Fallback Architecture**: Uses Google's **Gemini 3.8 Flash** REST API via `x-goog-api-key` header with an instant, zero-dependency **Deterministic Local Engine** fallback when an API key is absent, rate-limited (HTTP 429), or offline.
- 🔍 **True Landed Cost Ranking**: Compares multi-retailer offers by total landed cost ($\text{Sticker Price} + \text{Verified Shipping}$), preventing deceptive low-price listings from winning recommendation.
- 🛡️ **Zero Floating-Point Financial Precision**: Every monetary value is represented and calculated in integer paise. Zero IEEE-754 rounding drift.
- 🚫 **Unconfirmed Shipping Quarantine**: Offers without verified delivery costs are never treated as free delivery and cannot proceed through checkout.
- 💳 **PayPal Sandbox Integration**: End-to-end checkout with server-side price recalculation, order creation, buyer approval, and server-side capture verification.
- 🔒 **Enterprise Authentication & Token Revocation**: Argon2id password hashing and JWT token denylist on logout to prevent replay attacks.
- 📊 **Administrator Control Center**: Out-of-band CLI provisioning and protected dashboard for managing catalogue products and active offers.
- 📢 **Demo Data Transparency**: Prominent disclosures across the UI and API explicitly indicating simulated retailer offers.

---

## 3. System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        React 18 + Vite Frontend                        │
│            Tailwind CSS • Lucide Icons • @paypal/react-paypal-js        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST JSON
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          FastAPI Backend Core                          │
│                                                                        │
│   ┌───────────────────────────┐      ┌─────────────────────────────┐   │
│   │    AI Shopping Copilot    │      │    Landed Cost Engine       │   │
│   │   • Gemini 3.8 Flash REST │      │   • Integer Paise Math      │   │
│   │   • Regex/Token Fallback  │      │   • Multi-Offer Ranking     │   │
│   │   • Rate Limiting (15/m)  │      │   • Unknown Shipping Guard  │   │
│   └─────────────┬─────────────┘      └──────────────┬──────────────┘   │
│                 │                                   │                  │
│   ┌─────────────┴─────────────┐      ┌──────────────┴──────────────┐   │
│   │   Auth & Security Core    │      │    PayPal Sandbox Router    │   │
│   │   • Argon2id Hashing      │      │   • Server Price Recalc     │   │
│   │   • JWT Denylist Revoke   │      │   • Two-Step Capture Verify │   │
│   └───────────────────────────┘      └─────────────────────────────┘   │
└────────────────────┬────────────────────────────────┬──────────────────┘
                     │                                │
                     ▼                                ▼
       ┌───────────────────────────┐    ┌──────────────────────────┐
       │   SQLite / PostgreSQL     │    │  PayPal Sandbox REST API │
       │   SQLAlchemy 2.0 (Paise)  │    │  api-m.sandbox.paypal.com│
       └───────────────────────────┘    └──────────────────────────┘
```

---

## 4. Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 18, Vite 5, React Router v6, Tailwind CSS 3, Lucide React, `@paypal/react-paypal-js` |
| **Backend** | Python 3.10+, FastAPI 0.115+, Pydantic v2, SQLAlchemy 2.0, Uvicorn, HTTPX |
| **AI / NLP** | Google Gemini REST API (`gemini-3.8-flash`), deterministic regex/token fallback engine |
| **Database** | SQLite 3 (development / local evaluation) / PostgreSQL compatible |
| **Security** | Argon2id (`argon2-cffi`), PyJWT with database `jti` revocation, CORS middleware, slowapi rate-limiting |
| **Payments** | PayPal REST API (Sandbox mode) with server-side capture verification |
| **Testing** | Pytest (109 backend tests), Vitest + React Testing Library (25 frontend tests) |

---

## 5. AI Shopping Copilot & Fallback Engine

The Copilot is engineered with defense-in-depth reliability:

1. **Gemini 3.8 Flash Integration**:
   - Sends user requests to the native Gemini REST endpoint (`v1beta/models/{GEMINI_MODEL}:generateContent`).
   - Authenticates strictly using the `x-goog-api-key` HTTP header (never in query parameters or URLs).
   - Enforces a 5.0-second timeout to maintain snappy UI responsiveness.
   - Requires strict JSON structured output conforming to `CopilotExtractedIntent`.

2. **Deterministic Local Fallback Engine**:
   - Automatically activates if `GEMINI_API_KEY` is missing/empty, if Gemini returns HTTP 401/403/429, on network timeouts, or on malformed JSON.
   - Uses verified regular expressions and tokenizers to detect budget limits (`"under 28000"`, `"below ₹30,000"`, `"budget 45k"`), brands (`Sony`, `Apple`, `Dyson`), categories (`Audio`, `Wearables`), and key features.
   - Operates 100% offline with zero external dependencies.

3. **Catalogue Matching & True Landed Cost Ranking**:
   - Extracted criteria are matched against verified database records.
   - For candidate products, the backend evaluates all active retailer offers, adding item price and verified shipping fee in integer paise.
   - The winning offer is the one with the lowest confirmed landed cost.

---

## 6. Project Directory Structure

```
SmartCart_AI_Rebuild/
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI route controllers (auth, products, orders, copilot, admin)
│   │   ├── core/            # Config, security (Argon2id/JWT), database connection
│   │   ├── db/              # Database initialization & migrations
│   │   ├── models/          # SQLAlchemy ORM models (User, Product, RetailerOffer, Order, etc.)
│   │   ├── schemas/         # Pydantic v2 validation schemas (copilot, orders, auth, products)
│   │   ├── scripts/         # Seed demo catalogue & admin creation CLI
│   │   ├── services/        # AI Copilot service, recommendation engine, monetary math
│   │   └── main.py          # Application entrypoint & middleware configuration
│   ├── tests/               # 109 automated Pytest unit and integration tests
│   ├── .env.example         # Documented backend environment configuration template
│   ├── pytest.ini           # Pytest test configuration
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── api/             # API client modules (auth, products, orders, copilot)
│   │   ├── components/      # UI components (AICopilotBar, Navbar, Alert, PayPalCheckoutButton)
│   │   ├── context/         # AuthContext and state providers
│   │   ├── pages/           # Pages (Home, Products, ProductDetail, Checkout, Orders, Login, Admin)
│   │   └── test/            # 25 automated Vitest unit, component, and E2E tests
│   ├── package.json         # Frontend dependencies and test scripts
│   ├── vite.config.js       # Vite configuration
│   └── tailwind.config.js   # Tailwind CSS configuration
├── docs/
│   ├── DEMO_GUIDE.md        # Comprehensive evaluator walkthrough & architecture guide
│   └── DEMO_CHECKLIST.md    # Scoring and verification checklist for hackathon judges
├── DEMO_RUNBOOK.md          # Step-by-step hackathon local demo runbook
├── LICENSE                  # Open-source MIT License
└── README.md                # Project documentation (this file)
```

---

## 7. Installation & Quick Start (Windows PowerShell)

### Prerequisites
- **Python**: Version 3.10+ (tested on Python 3.15)
- **Node.js**: Version 18+ (tested on Node.js v24.20.0 with npm 11.19.0)

### Step 1: Clone the Repository
```powershell
git clone https://github.com/Amoljain4383/SmartCart-AI-Rebuild.git
cd SmartCart-AI-Rebuild
```

### Step 2: Backend Setup
```powershell
# Navigate to backend directory
cd backend

# Create and activate virtual environment (if not already created)
python -m venv ..\.venv
..\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
Copy-Item .env.example .env
# Edit .env if you wish to provide GEMINI_API_KEY or PAYPAL_CLIENT_ID (optional)

# Initialize database schema and seed simulated demo products
python -m app.db.init_db
python -m app.scripts.seed_demo_catalog

# Optional: Create an administrator account out-of-band
python -m app.scripts.create_admin --email admin@smartcart.demo --name "Demo Admin"
```

### Step 3: Start the Backend Server
```powershell
# From the backend/ directory:
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- API Base URL: `http://127.0.0.1:8000`
- Interactive OpenAPI Documentation: `http://127.0.0.1:8000/docs`

### Step 4: Frontend Setup & Launch
Open a second PowerShell terminal:
```powershell
cd D:\download\SmartCart_AI_Rebuild\frontend

# Install node dependencies
npm.cmd install

# Start Vite development server
npm.cmd run dev
```
- Web Application URL: `http://localhost:5173`

---

## 8. Verification & Automated Testing

### Full Backend Test Suite (109 Tests)
```powershell
cd D:\download\SmartCart_AI_Rebuild\backend
..\.venv\Scripts\python.exe -m pytest -v
```
**Results:** `109 passed` in ~5.9s.
- `test_copilot.py` (31 tests): Gemini REST headers, fallback regex, budget parsing, rate limiting, guest requests, error handling.
- `test_copilot_schemas.py` (12 tests): Pydantic validation, key normalization, budget caps.
- `test_monetary.py` (6 tests): Zero-float integer paise arithmetic, landed cost formula.
- `test_auth_phase2.py` (13 tests): Argon2id hashing, role enforcement, profile, security.
- `test_token_revocation.py` (8 tests): JWT `jti` denylist on logout, concurrent sessions.
- `test_phase3_catalogue.py` (11 tests): Landed cost ranking, search, unknown shipping rejection, recommendation summary.
- `test_phase4_orders_paypal.py` (15 tests): Server price recalculation, PayPal Sandbox create/capture, duplicate protection.
- `test_phase6_e2e.py` (5 tests): Full E2E buyer journey.
- `test_api_health.py` & `test_models.py` (8 tests): Health check, SQLAlchemy constraints.

### Full Frontend Test Suite (25 Tests)
```powershell
cd D:\download\SmartCart_AI_Rebuild\frontend
npm.cmd test
```
**Results:** `25 passed` across 6 test suites.
- `src/test/copilot.test.jsx` (12 tests): Copilot bar rendering, chips, Gemini/fallback badge, landed cost audit, empty states, null recommendation, unknown shipping alert, demo disclosure.
- `src/test/paypal.test.jsx` (4 tests): PayPal button rendering, order creation, capture confirmation, failure handling.
- `src/test/routes.test.jsx` (4 tests): ProtectedRoute & AdminRoute access guards.
- `src/test/auth.test.jsx` (2 tests): Authentication form submission & payload validation.
- `src/test/dashboard_api.test.jsx` (2 tests): Admin KPI counters & 401 token invalidation.
- `src/test/e2e_journey.test.jsx` (1 test): Complete 13-step buyer journey.

### Frontend Production Build
```powershell
cd D:\download\SmartCart_AI_Rebuild\frontend
npm.cmd run build
```
**Results:** Clean production build with zero warnings or errors.

---

## 9. PayPal Sandbox Integration Architecture

SmartCart AI adheres strictly to PayPal's secure server-side integration guidelines:

1. **Client Isolation**: The client never determines or passes order amounts to PayPal.
2. **Server Price Recalculation**: When a user selects an offer, the backend retrieves the product sticker price and verified shipping fee from database records in integer paise, recalculating the total.
3. **Sandbox Order Creation**: The backend communicates with PayPal Sandbox (`https://api-m.sandbox.paypal.com/v2/checkout/orders`) to generate an authoritative PayPal order ID.
4. **Buyer Approval**: The official `@paypal/react-paypal-js` button presents the buyer approval popup.
5. **Server-Side Capture Verification**: Upon approval, the backend executes the capture call directly with PayPal's API, verifying the captured currency and exact amount before updating the order status to `paid`.
6. **Unknown Shipping Guard**: Offers with unconfirmed shipping charges are rejected at the order creation endpoint (`HTTP 400 Bad Request`), preventing incomplete checkouts.

> **Note on Verification**: PayPal Sandbox checkout flows are comprehensively validated via automated test mocks in `backend/tests/test_phase4_orders_paypal.py` and `frontend/src/test/paypal.test.jsx`. Live sandbox capture requires valid PayPal Sandbox credentials configured in `.env`.

---

## 10. Security & Responsible Disclosure

- **Secret Isolation**: Real `.env` files, API keys, and SQLite database files are strictly excluded from version control via `.gitignore`.
- **Argon2id Password Storage**: Passwords are never stored in plaintext or reversible formats; salted hashes are generated via `argon2-cffi`.
- **JWT Denylist**: User logout immediately invalidates the token `jti` in a persistent database denylist.
- **Rate Limiting**: The AI Copilot endpoint is rate-limited to 15 requests per minute per IP to prevent quota exhaustion and abuse.
- **Simulated Demo Data Disclosure**: The catalogue currently operates on simulated demo retailer data for hackathon demonstration. All product prices, shipping rates, and seller profiles are simulated and clearly marked across both UI and API responses.

---

## 11. Known Limitations & Roadmap

- **Simulated Retailers**: Live scraping/API connections to commercial marketplaces (Amazon, Flipkart, Croma) are currently simulated to avoid bot-blocking and rate caps during judging.
- **Single-Item Checkout**: The current order pipeline processes one recommended retailer offer per checkout session. Multi-product cart consolidation is scheduled for the next release.
- **Currency Support**: The platform currently operates exclusively in Indian Rupees (INR) with integer paise representation. Multi-currency foreign exchange conversion is in planning.

---

## 12. License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
Copyright (c) 2026 SmartCart AI contributors.
