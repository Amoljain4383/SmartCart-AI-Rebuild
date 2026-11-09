# SmartCart AI — Hackathon Demonstration Runbook & Verification Guide

Welcome to the **SmartCart AI** demonstration runbook. This guide provides comprehensive, step-by-step instructions for judges, evaluators, and developers to run, verify, and evaluate the complete SmartCart AI system locally.

---

## 1. Project Architecture & Overview

SmartCart AI solves the deceptive e-commerce practice where surface sticker prices appear cheap but escalate at checkout due to hidden delivery charges. The system features an **AI Shopping Copilot** powered by **Gemini 3.8 Flash** with an offline **Deterministic Local Engine fallback**, coupled with an authoritative backend engine that audits **item sticker price + verified delivery fees** in integer paise to compute the **True Landed Cost**.

```
┌────────────────────────────────────────────────────────┐
│                   React 18 + Vite                      │
│            Tailwind CSS • Lucide Icons                 │
│         Official @paypal/react-paypal-js               │
└───────────────────────────┬────────────────────────────┘
                            │ REST API (JSON)
                            ▼
┌────────────────────────────────────────────────────────┐
│                   FastAPI Backend                      │
│      AI Shopping Copilot (Gemini 3.8 Flash REST)       │
│      Deterministic Regex/Token Fallback Engine         │
│      Argon2id Security • JWT Revocation Denylist       │
│      Integer Paise Engine (Zero IEEE-754 Drift)        │
└─────────────┬────────────────────────────┬─────────────┘
              │                            │
              ▼                            ▼
┌───────────────────────────┐ ┌──────────────────────────┐
│   SQLite / PostgreSQL     │ │  PayPal Sandbox REST API │
│   SQLAlchemy 2.0 (Paise)  │ │   Server Capture Verify  │
└───────────────────────────┘ └──────────────────────────┘
```

---

## 2. Quick Start: Launching the Application (Windows PowerShell)

### A. Prerequisites
- **Python**: 3.10+ (tested on Python 3.15 with virtual environment in `.venv`)
- **Node.js**: v18+ (tested on Node.js v24.20.0 with npm 11.19.0)

### B. Launching the Backend API Server
```powershell
# Open Terminal 1
cd D:\download\SmartCart_AI_Rebuild\backend

# Run database initialization & seed demo catalogue (safe and idempotent)
..\.venv\Scripts\python.exe -m app.db.init_db
..\.venv\Scripts\python.exe -m app.scripts.seed_demo_catalog

# Optional: Set GEMINI_API_KEY in backend/.env to use Gemini 3.8 Flash
# If no key is set, the Copilot automatically runs via the Deterministic Local Engine

# Start the FastAPI server
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- API Base URL: `http://127.0.0.1:8000`
- Interactive OpenAPI Docs: `http://127.0.0.1:8000/docs`

### C. Launching the Frontend Client
```powershell
# Open Terminal 2
cd D:\download\SmartCart_AI_Rebuild\frontend

# Launch the Vite development server
npm.cmd run dev
```
- Frontend Application URL: `http://localhost:5173`

---

## 3. Automated Test Suite Verification

Both backend and frontend feature 100% automated test suites covering authentication, landed-cost ranking, tamper-proof ordering, PayPal capture, and UI route protections.

### A. Run Full Backend Test Suite (109 Tests)
```powershell
cd D:\download\SmartCart_AI_Rebuild\backend
..\.venv\Scripts\python.exe -m pytest -v
```
**Results:** `109 passed` in ~5.9s.
- `test_copilot.py` (31 tests): Gemini REST headers (`x-goog-api-key`), fallback regex, budget parsing, rate limiting (15 req/min), guest/auth requests, error handling.
- `test_copilot_schemas.py` (12 tests): Pydantic validation, key normalization, budget caps.
- `test_monetary.py` (6 tests): Integer paise math, zero IEEE-754 floating-point drift.
- `test_auth_phase2.py` (13 tests): Argon2id hashing, registration role enforcement, login, profile.
- `test_token_revocation.py` (8 tests): JWT `jti` denylist, logout revocation, concurrent session isolation.
- `test_phase3_catalogue.py` (11 tests): Landed cost ranking, search, unknown shipping rejection, AI recommendation.
- `test_phase4_orders_paypal.py` (15 tests): Server price recalculation, PayPal Sandbox create/capture, duplicate capture protection.
- `test_phase6_e2e.py` (5 tests): Full E2E flows (Auth → Search → Recommendation → Orders → PayPal capture).
- `test_api_health.py` & `test_models.py` (8 tests): Health check, SQLAlchemy constraints.

### B. Run Full Frontend Test Suite (25 Tests)
```powershell
cd D:\download\SmartCart_AI_Rebuild\frontend
npm.cmd test
```
**Results:** `25 passed` across 6 test suites.
- `copilot.test.jsx` (12 tests): Copilot bar rendering, chips, Gemini/fallback mode badge, landed cost audit, empty states, null recommendation, unknown shipping alert, demo disclosure.
- `paypal.test.jsx` (4 tests): Official PayPal Sandbox SDK creation, buyer approval capture, and error states.
- `routes.test.jsx` (4 tests): `ProtectedRoute` and `AdminRoute` guard redirection and permission checks.
- `auth.test.jsx` (2 tests): Login form submission and registration payload verification.
- `dashboard_api.test.jsx` (2 tests): 401 token invalidation handling and admin dashboard rendering.
- `e2e_journey.test.jsx` (1 test): Full 13-step buyer journey simulation.

### C. Verify Frontend Production Build
```powershell
cd D:\download\SmartCart_AI_Rebuild\frontend
npm.cmd run build
```
**Results:** `vite build` completed with **0 errors, 0 warnings**.

---

## 4. Live Hackathon Demonstration Walkthrough

Follow this 14-step walkthrough in your browser at `http://localhost:5173`:

| Step | Action | Expected Result |
| :---: | :--- | :--- |
| **1** | Open Home Page (`/`) | Displays hero section, AI Shopping Copilot bar, value pillars, and persistent simulated demo disclosure banner. |
| **2** | **Test AI Shopping Copilot** | In the Copilot input on Home or Products page, enter: `Sony WH-1000XM5 under ₹28,000 with noise cancelling` (or click a suggestion chip). |
| **3** | **Inspect Copilot Analysis** | The Copilot displays: 1) Active engine badge (`Gemini 3.8 Flash` or `Deterministic Local Engine`), 2) Extracted intent pills (Query, Category: Audio, Brand: Sony, Budget Cap: ₹28,000, Features), 3) Natural language explanation, 4) Demo-data notice callout, and 5) Top AI Best Value recommendation card with True Landed Cost audit. |
| **4** | Click **Create Account** (`/register`) | Fill in Name, Email, and Password (min 8 chars). Click **Register & Continue**. |
| **5** | Account Created | Automatically signed in with `role="user"` enforced server-side. User initials badge appears in top navigation. |
| **6** | Catalogue Search | In the standard catalogue search, type `Sony` or `Kindle`. Filters matching catalogue products instantly. |
| **7** | Open Product Details | Click **Compare** on the Sony WH-1000XM5 product card. |
| **8** | Inspect Landed Cost Table | View competing retailer offers. Observe that **SonicSound Store** has a lower base sticker price (₹25,999) + ₹499 shipping = **₹26,498 True Landed Cost**, beating ElectroMart (₹26,990) and GadgetWorld (₹27,499). |
| **9** | View Deterministic Recommendation | The **SmartCart AI Recommendation** card highlights SonicSound Store and shows exact savings (e.g. saves ₹492 vs next option) using our deterministic integer paise engine. |
| **10** | Proceed to Checkout | Click **Select for Checkout**. Address form opens pre-filled with destination. |
| **11** | Confirm Address | Click **Confirm Address & Proceed to Payment**. Backend recalculates total in integer paise and creates order in `pending` status. |
| **12** | PayPal Sandbox Checkout | The official PayPal Sandbox button renders. Clicking triggers server-side order creation (`POST /api/orders/{id}/paypal/create`), loads buyer approval modal, and on approval executes server-side verified capture (`POST /api/orders/{id}/paypal/capture`). |
| **13** | View Verified Order Receipt | Automatically redirects to `/orders/{id}?payment_success=true`. Displays **Paid & Verified** badge, PayPal Order ID, Capture ID, itemized line items, and delivery address. |
| **14** | Sign Out | Click the logout icon. Server revokes JWT `jti` in denylist. Attempting to reopen `/orders` immediately redirects to `/login`. |

---

## 5. Administrator Control Center Walkthrough

Admin capabilities are strictly separated from public registration.

### A. Provisioning an Administrator (Private CLI)
To provision an administrator, run the backend CLI tool:
```powershell
cd D:\download\SmartCart_AI_Rebuild\backend
..\.venv\Scripts\python.exe -m app.scripts.create_admin --email admin@smartcart.local --name "Demo Admin"
```
You will be prompted to enter a password securely using Python's `getpass` (no password echo in terminal history).

### B. Accessing the Admin Panel
1. Sign in at `http://localhost:5173/login` using your provisioned admin credentials.
2. The purple **Admin Panel** badge appears in the top navigation.
3. Open `http://localhost:5173/admin`:
   - **Catalogue Metrics**: Real-time product counts, active products, linked offers, and system status.
   - **Product Management Tab**: Toggle products active/inactive with live patch updates; create new products; edit existing metadata.
   - **Retailer Offers Tab**: Select any product to inspect competing retailer offers; add new retailer offers; adjust pricing and shipping; toggle active status.
4. Sign out. Attempting to open `/admin` as a normal user or unauthenticated visitor redirects to `/` or `/login`.

---

## 6. Core Engineering & Security Principles

1. **Integer Paise Financial Precision**: All product prices, shipping rates, and order totals are stored and calculated in integer paise ($1\text{ INR} = 100\text{ paise}$). Zero floating-point rounding errors.
2. **Server-Side Authoritative Pricing**: Client-side prices are never trusted. When creating an order, the backend re-fetches active offers from the database and recalculates totals.
3. **Argon2id Cryptographic Security**: Industry-standard Argon2id password hashing via `argon2-cffi`. Passwords are never stored in plaintext or logged.
4. **JWT Token Revocation via Database Denylist**: Access tokens include a unique UUID4 `jti` and explicit type claims. Logging out registers the `jti` in the database `revoked_tokens` table. Expired or revoked tokens cannot access protected endpoints.
5. **Dual-Mode AI Shopping Copilot**: Combines Gemini 3.8 Flash via native REST with an offline deterministic regex parser. The system never goes down due to external API failures.
6. **Rate-Limiting & Quota Protection**: Copilot requests are bounded at 15 req/min per IP to prevent API exhaustion.
7. **PayPal Sandbox Server Capture**: The frontend never captures payments directly. The backend captures and verifies the exact captured amount and currency before transitioning orders to `paid`, with atomic duplicate-capture protection.
8. **Simulated Demo Data Disclosures**: All products, retailer offers, and checkouts are prominently labeled as simulated demonstration data.
