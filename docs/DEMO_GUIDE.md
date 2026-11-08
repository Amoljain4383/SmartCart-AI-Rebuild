# SmartCart AI — Evaluator Demonstration Guide

This guide provides end-to-end instructions for running, evaluating, and troubleshooting the **SmartCart AI** local demonstration environment.

---

## 1. Prerequisites

Ensure the following runtimes and packages are present on your evaluation machine:

- **Operating System**: Windows 10/11, macOS, or Linux (Windows PowerShell commands provided below)
- **Python**: Version 3.10+ (tested on Python 3.15 with virtual environment in `.venv/`)
- **Node.js**: Version 18+ (tested on Node.js v24.20.0 with npm 11.19.0)
- **Web Browser**: Google Chrome, Microsoft Edge, Mozilla Firefox, or Safari

---

## 2. Exact PowerShell Setup Commands

Open a PowerShell terminal in the project root directory:

```powershell
# Navigate to project root
cd D:\download\SmartCart_AI_Rebuild

# Verify Python and Node environments
.\.venv\Scripts\python.exe --version
npm.cmd --version
```

If dependencies need to be verified or refreshed:

```powershell
# Backend virtual environment dependencies
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt

# Frontend node_modules
cd frontend
npm.cmd install
cd ..
```

---

## 3. Database Initialization & Demo Catalogue Seeding

SmartCart AI uses SQLite (`smartcart.db`) for zero-configuration local evaluation.

Execute the following commands from the `backend/` directory:

```powershell
cd D:\download\SmartCart_AI_Rebuild\backend

# 1. Initialize database schema & run column migrations
..\.venv\Scripts\python.exe -m app.db.init_db

# 2. Seed realistic simulated demo products and competing multi-retailer offers
..\.venv\Scripts\python.exe -m app.scripts.seed_demo_catalog
```

> **Note**: `seed_demo_catalog` is safe and idempotent. To reset existing products and reseed fresh records, add the `--reset` flag:
> `..\.venv\Scripts\python.exe -m app.scripts.seed_demo_catalog --reset`

---

## 4. Private Administrator Account Provisioning

In accordance with strict security requirements, administrator accounts **cannot** be registered through the public web frontend. Administrators are provisioned out-of-band via the secure backend CLI:

```powershell
cd D:\download\SmartCart_AI_Rebuild\backend

# Run the admin creation CLI
..\.venv\Scripts\python.exe -m app.scripts.create_admin --email admin@smartcart.local --name "Demo Administrator"
```

The CLI will prompt you to enter and confirm the admin password securely using Python's `getpass` library:
- **Email**: `admin@smartcart.local`
- **Password Prompt**: Enter a strong password (minimum 8 characters, at least 1 uppercase, 1 lowercase, 1 digit, 1 special symbol).
- *Terminal history will NOT display or store the typed password.*

---

## 5. PayPal Sandbox Configuration

SmartCart AI integrates with the official PayPal REST API in Sandbox mode. Client IDs and secrets are managed via environment variables.

### Backend PayPal Configuration
The backend reads environment variables from `backend/.env` (or defaults in `app/core/config.py`):

```ini
# backend/.env (Placeholders shown — never commit real secrets)
PAYPAL_MODE=sandbox
PAYPAL_CLIENT_ID=sandbox_client_id_placeholder
PAYPAL_CLIENT_SECRET=sandbox_client_secret_placeholder
PAYPAL_BASE_URL=https://api-m.sandbox.paypal.com
PAYPAL_CURRENCY=INR
```

### Frontend PayPal Configuration
The frontend reads public variables from `frontend/.env`:

```ini
# frontend/.env
VITE_API_URL=http://127.0.0.1:8000
VITE_PAYPAL_CLIENT_ID=your_paypal_sandbox_client_id
```

> **Sandbox Mode Behavior**:
> - When `VITE_PAYPAL_CLIENT_ID` is set to `test` or a placeholder, the frontend checkout button renders an informative sandbox configuration banner to prevent invalid network requests.
> - When valid Sandbox credentials from [developer.paypal.com](https://developer.paypal.com) are supplied, the official PayPal SDK modal loads for buyer approval.
> - All payments are strictly captured and verified server-side.

---

## 6. Service Startup Commands

### Terminal 1: Backend API Server
```powershell
cd D:\download\SmartCart_AI_Rebuild\backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- **API Base URL**: `http://127.0.0.1:8000`
- **Interactive Swagger Documentation**: `http://127.0.0.1:8000/docs`
- **Health Check Endpoint**: `http://127.0.0.1:8000/api/v1/health`

### Terminal 2: Frontend Client
```powershell
cd D:\download\SmartCart_AI_Rebuild\frontend
npm.cmd run dev
```
- **Web Application URL**: `http://localhost:5173`

---

## 7. Test User Instructions

For evaluating user journeys, you can create a test buyer account directly via the UI or use standard test credentials:

- **Option A (Create New Buyer)**:
  - Navigate to `http://localhost:5173/register`
  - Name: `Jane Doe`
  - Email: `buyer@example.com` (or any valid email)
  - Password: `Password123!`
- **Option B (Admin Sign In)**:
  - Navigate to `http://localhost:5173/login`
  - Email: `admin@smartcart.local`
  - Password: *(Password entered during CLI provisioning in Step 4)*

---

## 8. Complete Evaluator Demonstration Walkthrough

Follow this 13-step sequence in your browser to evaluate all platform capabilities:

| Step | Action | Page / Route | Evaluator Verification Checklist |
| :---: | :--- | :--- | :--- |
| **1** | Open Home Page | `http://localhost:5173/` | Hero section loads; core value proposition ("True Landed Cost") displayed; persistent "Simulated Demo Data" warning banner visible. |
| **2** | Create Buyer Account | `http://localhost:5173/register` | Enter Name, Email, and Password. Submit. Verifies client-side validation and backend Argon2id password hashing. |
| **3** | Auto-Login & Navigation | `http://localhost:5173/` | Redirects automatically after registration. User avatar/initials appear in navigation. JWT stored securely in browser storage. |
| **4** | Catalogue & Search | `http://localhost:5173/` | Type `Sony` or `WH-1000XM5` into the search box. Instant filtering returns the flagship Sony headphones card with badge. |
| **5** | Product Comparison | Click **Compare** on Sony card | Route transitions to `/products/{id}`. Displays high-resolution image, specs, and multi-retailer offer comparison matrix. |
| **6** | Audit Landed Costs | Retailer Offers Table | Observe offer rows: <br>• **SonicSound Store**: Sticker ₹25,999 + ₹499 Shipping = **₹26,498 Landed Cost** (Rank #1)<br>• **ElectroMart**: Sticker ₹26,990 + ₹0 Shipping = **₹26,990 Landed Cost** (Rank #2)<br>• **GadgetWorld**: Sticker ₹27,499 + ₹0 Shipping = **₹27,499 Landed Cost** (Rank #3)<br>Demonstrates that the lowest base price offer wins only after factoring in real shipping fees. |
| **7** | AI Recommendation | Recommendation Card | Evaluates offline deterministic engine. Displays best recommended offer, delivery trade-offs, and exact computed savings (₹492 savings). |
| **8** | Initiate Checkout | Click **Select for Checkout** | Navigates to `/checkout/{id}/{offer_id}`. Delivery address form appears with pre-filled defaults. |
| **9** | Confirm Address | Click **Confirm Address** | Backend creates order in `pending` status. Total is authoritatively calculated on server in integer paise (₹26,498.00 / 2,649,800 paise). |
| **10** | PayPal Checkout Interface | Checkout Screen | Official PayPal Sandbox checkout component loads via `@paypal/react-paypal-js`. Triggers server-side order creation. |
| **11** | Order Receipt | `/orders/{order_id}` | Order details display with status badge, line items breakdown (item price + shipping), and delivery destination. |
| **12** | Order History | `http://localhost:5173/orders` | Displays chronological list of buyer's past orders with status chips (`pending` / `paid`). Direct access to view receipts. |
| **13** | Sign Out & Route Guard | Click **Sign Out** | JWT `jti` is revoked on backend denylist. Navigating back to `/orders` or `/checkout` immediately redirects to `/login`. |

### Administrator Control Center Walkthrough (Steps 14–16)

| Step | Action | Route | Evaluator Verification Checklist |
| :---: | :--- | :--- | :--- |
| **14** | Admin Sign In | `http://localhost:5173/login` | Log in with `admin@smartcart.local`. Purple **Admin Panel** link appears in navigation bar. |
| **15** | View Dashboard KPIs | `http://localhost:5173/admin` | Live metric cards display Total Products, Active Offers, System Health, and Database connectivity without any `undefined` values. |
| **16** | Manage Catalogue | Products / Offers Tabs | Toggle active/inactive statuses for products and offers; verify that deactivated items disappear from the public buyer catalogue immediately. |

---

## 9. Troubleshooting Guide

| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| **Backend fails with `Access is denied` on Python executable** | Windows AppData symlink execution policy | Run the command pointing directly to `.venv\Scripts\python.exe` or execute inside PowerShell with standard user rights. |
| **Frontend displays `Failed to fetch` or CORS errors** | Backend server is not running on port 8000 | Ensure Terminal 1 is running: `..\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000`. Verify `backend/.env` CORS origins include `http://localhost:5173`. |
| **PayPal button shows "Client ID not configured"** | `VITE_PAYPAL_CLIENT_ID` is unset or `test` | This is expected in offline demo mode. To enable active Sandbox buttons, register a free test sandbox app at [developer.paypal.com](https://developer.paypal.com) and paste the Sandbox Client ID into `frontend/.env`. |
| **Admin Panel inaccessible (403 Forbidden)** | Logged in as a standard user (`role="user"`) | Standard accounts cannot view `/admin`. Log out and log back in with the administrator account provisioned via `create_admin`. |
| **Database missing products or empty catalogue** | Seed script was not executed | Run `cd backend; ..\.venv\Scripts\python.exe -m app.scripts.seed_demo_catalog`. |

---

## 10. Stop and Restart Commands

### Stopping the Applications
To stop running processes cleanly:
- In Terminal 1 (Backend): Press `Ctrl + C`
- In Terminal 2 (Frontend): Press `Ctrl + C`

### Quick Restart One-Liners

**Backend Restart**:
```powershell
cd D:\download\SmartCart_AI_Rebuild\backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Frontend Restart**:
```powershell
cd D:\download\SmartCart_AI_Rebuild\frontend
npm.cmd run dev
```

---

*SmartCart AI — Demonstrating True Landed Cost Transparency with Full-Stack Verification.*
