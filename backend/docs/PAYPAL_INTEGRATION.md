# SmartCart AI — PayPal Sandbox Integration Guide

## 1. Overview & Demonstration Nature

> [!IMPORTANT]
> **Simulated Demonstration Checkout Only:**
> SmartCart AI's PayPal checkout is a demonstration feature running in the **PayPal Sandbox** environment.
> - **No real money is charged** (transactions use PayPal Sandbox fictitious balances).
> - **No orders are dispatched** to external third-party retailers (e.g. Amazon, Croma, SonicSound).
> - The purchase confirms an order record in SmartCart's database for demonstration, testing, and receipt generation.

---

## 2. Obtaining PayPal Sandbox Credentials

1. Go to the [PayPal Developer Portal](https://developer.paypal.com/) and sign in with your PayPal account.
2. Navigate to **Dashboard** $\rightarrow$ **Apps & Credentials**.
3. Under the **Sandbox** tab, create a new REST API app (e.g., "SmartCart Demo").
4. Copy the **Client ID** and **Secret Key**.
5. Under **Sandbox Accounts**, note the pre-created Personal (buyer) and Business (merchant) accounts along with their sandbox test logins.

---

## 3. Required Environment Variables

Configure these in `backend/.env` (modeled after `backend/.env.example`):

| Variable | Default | Description |
| :--- | :--- | :--- |
| `PAYPAL_MODE` | `sandbox` | PayPal environment (`sandbox` or `live`) |
| `PAYPAL_CLIENT_ID` | *(placeholder)* | Server-side REST API Sandbox Client ID |
| `PAYPAL_CLIENT_SECRET` | *(placeholder)* | Server-side REST API Sandbox Secret Key (NEVER expose to frontend) |
| `PAYPAL_BASE_URL` | `https://api-m.sandbox.paypal.com` | PayPal REST API Sandbox endpoint |
| `PAYPAL_CURRENCY` | `INR` | Configured merchant currency for checkout |
| `PAYPAL_WEBHOOK_ID` | *(placeholder)* | Optional Sandbox Webhook ID |

---

## 4. Financial Precision & Currency Handling

1. **Integer Paise Storage**: SmartCart stores all catalogue, shipping, and order amounts in **integer paise** (e.g. ₹26,498.00 = `2649800` paise).
2. **Two-Decimal String Conversion**: PayPal's Orders v2 API mandates amounts as stringified two-decimal values (e.g. `"26498.00"`). The backend performs this conversion deterministically using `paise_to_paypal_amount_str()` without floating-point arithmetic.
3. **Currency Mismatch Safeguard**: If `order.currency` differs from `PAYPAL_CURRENCY`, checkout is rejected with HTTP 400 to prevent silent, arbitrary currency conversions.

---

## 5. Order & Payment Lifecycle

```
[Customer Cart]
       │
       ▼ (1) POST /api/orders
   [Status: pending] ── Recalculates exact prices & shipping in integer paise
       │
       ▼ (2) POST /api/orders/{id}/paypal/create
[Status: paypal_created] ── Calls PayPal Sandbox Orders v2 (Server-Side)
       │
       ▼ (3) Buyer Approves in PayPal Modal (Frontend SDK)
       │
       ▼ (4) POST /api/orders/{id}/paypal/capture
    [Status: paid] ── Server-to-server capture verification (amount & currency match)
```

### Valid State Transitions
- `pending` $\rightarrow$ `paypal_created`
- `paypal_created` $\rightarrow$ `paid`
- `pending` / `paypal_created` $\rightarrow$ `failed` or `cancelled`
- `paid` and `cancelled` are terminal states. Invalid transitions are rejected with HTTP 400.

---

## 6. Endpoints Reference

### 6.1 Create Order (`POST /api/orders`)
- **Access**: Authenticated user.
- **Payload**:
  ```json
  {
    "items": [
      {"offer_id": "uuid-here", "quantity": 1}
    ],
    "shipping_address": {"city": "Bengaluru", "country": "IN"},
    "idempotency_key": "unique-client-key"
  }
  ```
- **Response**: `OrderResponse` with server-calculated integer paise totals.

### 6.2 Create PayPal Order (`POST /api/orders/{order_id}/paypal/create`)
- **Access**: Authenticated owner or admin.
- Calls PayPal Sandbox `/v2/checkout/orders` with `PayPal-Request-Id` for idempotency.
- Returns `{ "order_id": "...", "paypal_order_id": "...", "amount": "26498.00", "currency": "INR" }`.

### 6.3 Capture PayPal Payment (`POST /api/orders/{order_id}/paypal/capture`)
- **Access**: Authenticated owner or admin.
- Verifies capture status == `"COMPLETED"`.
- **Strict Verification**: Confirms `captured_amount == order.paypal_amount_str` and `captured_currency == order.currency`.
- **Duplicate Protection**: Repeated capture requests for an already paid order return the confirmed receipt safely without double-charging.

### 6.4 Order History (`GET /api/orders` & `GET /api/orders/{order_id}`)
- Users can view only their own orders. Unauthorized cross-user requests receive HTTP 404.

---

## 7. Testing with Mocked Responses

All automated tests mock PayPal API calls via `monkeypatch` in Pytest. No outbound network requests or fictitious Sandbox transactions occur during test execution:

```powershell
cd backend
..\.venv\Scripts\pytest.exe -v tests/test_phase4_orders_paypal.py
```
