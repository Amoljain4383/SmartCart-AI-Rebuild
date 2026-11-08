# SmartCart AI — Evaluator Presentation Checklist

A concise, high-impact checklist for evaluating and scoring the **SmartCart AI** platform.

---

## 1. Pre-Demonstration Environment Readiness

- [ ] **Backend Service**: Running at `http://127.0.0.1:8000` (FastAPI with OpenAPI docs at `/docs`)
- [ ] **Frontend Application**: Running at `http://localhost:5173` (Vite + React)
- [ ] **Database Seeded**: 5 simulated products with 15 competing multi-retailer offers (`smartcart.db`)
- [ ] **Administrator Provisioned**: Created via out-of-band CLI `python -m app.scripts.create_admin`
- [ ] **Test Suites Verified**:
  - [ ] Backend: 66 / 66 tests passing (`pytest -v`)
  - [ ] Frontend: 13 / 13 tests passing (`npm test`)
  - [ ] Build: Production bundle builds cleanly with zero errors (`npm run build`)

---

## 2. Core Buyer Journey Walkthrough Checklist

| Item | Feature | Evaluator Verification Criterion | Status |
| :---: | :--- | :--- | :---: |
| **01** | **Landing Experience** | Clean UI, value proposition explanation, and persistent "Simulated Demo Data" disclosure banner. | [ ] |
| **02** | **Account Creation** | Form registers new user (`role="user"` enforced server-side); client never sends role payload. | [ ] |
| **03** | **Authentication** | Automatic sign-in after registration; user initials avatar in top navbar; JWT stored securely. | [ ] |
| **04** | **Instant Search** | Fast filtering by product name (e.g., "Sony WH-1000XM5") and category tags. | [ ] |
| **05** | **Multi-Retailer Comparison** | Itemized table displaying Base Price, Verified Shipping, Delivery ETA, and Return Policy. | [ ] |
| **06** | **True Landed Cost Ranking** | Transparent sorting by total cost ($\text{Price} + \text{Shipping}$); offers with hidden fees lose top rank. | [ ] |
| **07** | **AI Recommendation** | Deterministic rule-based engine card displays clear trade-off summary and exact computed savings. | [ ] |
| **08** | **Order Initialization** | Order created with authoritative server recalculation in integer paise; rejects client tampering. | [ ] |
| **09** | **PayPal Sandbox Component** | Official `@paypal/react-paypal-js` button renders cleanly; triggers server order creation. | [ ] |
| **10** | **Server Capture & Receipt** | Server captures sandbox payment; verified receipt displays itemized breakdown and delivery address. | [ ] |
| **11** | **Order History** | `/orders` displays historical user orders with real-time status chips (`pending` / `paid`). | [ ] |
| **12** | **Logout & Token Denylist** | Signing out revokes JWT `jti` in database denylist; protected pages redirect immediately to `/login`. | [ ] |

---

## 3. Administrator Control Center Checklist

| Item | Feature | Evaluator Verification Criterion | Status |
| :---: | :--- | :--- | :---: |
| **13** | **Role-Based Access Control** | Standard users attempting to access `/admin` receive 403 Forbidden or redirect. | [ ] |
| **14** | **Admin Navigation** | Admin badge and navigation link only visible to authenticated users with `role="admin"`. | [ ] |
| **15** | **Dashboard Metrics** | Live KPI counters for Total Products, Active Offers, and System Status render without `undefined`. | [ ] |
| **16** | **Catalogue Management** | Toggle products and offers active/inactive; updates reflect immediately in public buyer view. | [ ] |

---

## 4. Architectural & Security Principles Checklist

| Principle | Verification Mechanism | Status |
| :--- | :--- | :---: |
| **Integer Paise Precision** | All monetary amounts stored as integer paise ($1\text{ INR} = 100\text{ paise}$); zero floating-point drift. | [ ] |
| **Argon2id Password Security** | Password hashes generated using Argon2id (`argon2-cffi`); raw passwords never logged or returned. | [ ] |
| **JWT Revocation Denylist** | Every access token carries a unique `jti`; logout adds `jti` to database denylist. | [ ] |
| **Zero Client Trust** | Order total amounts recalculated authoritatively on backend from active database offers. | [ ] |
| **No Hardcoded Secrets** | Credentials loaded strictly via environment variables; placeholder keys used for demo safety. | [ ] |
| **Offline Fallback Engine** | Recommendation engine works 100% offline without external paid LLM API dependency. | [ ] |

---

*Evaluator Signature / Notes:*
