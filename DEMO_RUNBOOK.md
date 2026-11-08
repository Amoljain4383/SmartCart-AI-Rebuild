# SmartCart AI — Hackathon Demonstration Runbook & Verification Guide

Welcome to the **SmartCart AI** demonstration guide. This document provides step-by-step instructions for judges, evaluators, and developers to run, verify, and evaluate the complete SmartCart AI system locally.

---

## 1. Project Architecture & Overview

SmartCart AI solves the deceptive e-commerce practice where surface sticker prices appear cheap but double at checkout due to hidden delivery fees. The system audits **item sticker price + verified shipping fees** to compute the **True Landed Cost** across competing retailers.

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
│    Argon2id Security • JWT Revocation Denylist         │
│     Integer Paise Engine • Deterministic AI            │
└─────────────┬────────────────────────────┬─────────────┘
              │                            │
              ▼                            ▼
┌───────────────────────────┐ ┌──────────────────────────┐
│   SQLite / PostgreSQL     │ │  PayPal Sandbox REST API │
│   SQLAlchemy 2.0 (Paise)  │ │   Server Capture Verify  │
└───────────────────────────┘ └──────────────────────────┘
```

---

## 2. Quick Start: Launching the Application

### A. Prerequisites
- **Python**: 3.10+ (tested on Python 3.15 with `.venv`)
- **Node.js**: v18+ (tested on Node v24.20.0 with npm 11.19.0)

### B. Launching the Backend API Server
```powershell
# Open Terminal 1
cd D:\download\SmartCart_AI_Rebuild\backend

# Run database initialization & seed demo catalogue (idempotent)
..\.venv\Scripts\python.exe -m app.scripts.init_db
..\.venv\Scripts\python.exe -m app.scripts.seed_demo_catalog

# Start the FastAPI server
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- API Base: `http://127.0.0.1:8000`
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

### A. Run Full Backend Test Suite (66 Tests)
```powershell
cd D:\download\SmartCart_AI_Rebuild\backend
..\.venv\Scripts\python.exe -m pytest -v
```
**Results:** `66 passed` in ~5.5s.
- `test_api_health.py` (2 tests): Health and root endpoints.
- `test_models.py` (6 tests): SQLAlchemy schema constraints, unique keys, and Argon2id.
- `test_monetary.py` (6 tests): Integer paise math, zero IEEE-754 floating-point drift.
- `test_auth_phase2.py` (13 tests): Argon2id hashing, registration role enforcement, login, profile.
- `test_token_revocation.py` (8 tests): JWT `jti` denylist, logout revocation, concurrent session isolation.
- `test_phase3_catalogue.py` (11 tests): Landed cost ranking, search, unknown shipping rejection, AI recommendation.
- `test_phase4_orders_paypal.py` (15 tests): Server price recalculation, PayPal Sandbox create/capture, duplicate capture protection.
- `test_phase6_e2e.py` (5 tests): Full E2E flows (Auth $\rightarrow$ Search $\rightarrow$ Recommendation $\rightarrow$ Orders $\rightarrow$ PayPal capture).

### B. Run Full Frontend Test Suite (13 Tests)
```powershell
cd D:\download\SmartCart_AI_Rebuild\frontend
npm.cmd test
```
**Results:** `13 passed` across 5 test suites.
- `auth.test.jsx`: Login form submission and registration payload verification (no role sent).
- `routes.test.jsx`: `ProtectedRoute` and `AdminRoute` guard redirection and permission checks.
- `paypal.test.jsx`: Official PayPal Sandbox SDK creation, buyer approval capture, and error states.
- `dashboard_api.test.jsx`: 401 token invalidation handling and admin dashboard rendering.
- `e2e_journey.test.jsx`: Full 13-step buyer journey simulation.

### C. Verify Frontend Production Build
```powershell
cd D:\download\SmartCart_AI_Rebuild\frontend
npm.cmd run build
```
**Results:** `vite build` completed with **0 errors, 0 warnings**.

---

## 4. Live Hackathon Demonstration Walkthrough

Follow this 13-step walkthrough in your browser at `http://localhost:5173`:

| Step | Action | Expected Result |
| :---: | :--- | :--- |
| **1** | Open Home Page (`/`) | Displays hero section, value pillars, quick search bar, and persistent simulated demo disclosure banner. |
| **2** | Click **Create Account** (`/register`) | Fill in Name, Email, and Password (min 8 chars). Click **Register & Continue**. |
| **3** | Account Created | Automatically signed in with `role="user"`. User initials badge appears in top navigation. |
| **4** | Search for **Sony WH-1000XM5** | Type `Sony` or `WH-1000XM5` in the search bar. Shows Sony WH-1000XM5 with Best Landed Cost. |
| **5** | Open Product Details | Click **Compare** on the Sony product card. |
| **6** | Inspect Landed Cost Table | View competing retailer offers. Observe that **SonicSound Store** has a lower base sticker price (₹25,999) + ₹499 shipping = **₹26,498 True Landed Cost**, beating ElectroMart (₹26,990) and GadgetWorld (₹27,499). |
| **7** | View AI Recommendation | The **SmartCart AI Recommendation** card highlights SonicSound Store and shows exact savings (e.g. saves ₹492 vs next option) using our deterministic offline engine. |
| **8** | Proceed to Checkout | Click **Select for Checkout**. Address form opens pre-filled with destination. |
| **9** | Confirm Address | Click **Confirm Address & Proceed to Payment**. Backend recalculates total in integer paise and creates order in `pending` status. |
| **10** | PayPal Sandbox Checkout | The official PayPal Sandbox button renders. Clicking triggers server-side order creation (`POST /api/orders/{id}/paypal/create`), loads buyer approval modal, and on approval executes server-side verified capture (`POST /api/orders/{id}/paypal/capture`). |
| **11** | View Verified Order Receipt | Automatically redirects to `/orders/{id}?payment_success=true`. Displays **Paid & Verified** badge, PayPal Order ID, Capture ID, itemized line items, and delivery address. |
| **12** | Inspect Order History | Click **My Orders** in the header. Shows historical orders with status badges. |
| **13** | Sign Out | Click the logout icon. Server revokes JWT `jti` in denylist. Attempting to reopen `/orders` immediately redirects to `/login`. |

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
5. **Offline Deterministic Recommendation Engine**: Zero external paid AI dependencies. Instant, transparent, and mathematically verifiable recommendations.
6. **PayPal Sandbox Server Capture**: The frontend never captures payments directly. The backend captures and verifies the exact captured amount and currency before transitioning orders to `paid`, with atomic duplicate-capture protection.
7. **Simulated Demo Data Disclosures**: All products, retailer offers, and checkouts are prominently labeled as simulated demonstration data.
