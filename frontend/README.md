# SmartCart AI — Frontend Application

Modern React 18 + Vite frontend for **SmartCart AI**, built with Tailwind CSS, Lucide icons, and React Router v6.

## 🚀 Quick Start

### 1. Prerequisites
- Node.js v18+ (tested on v24.20.0)
- Backend running at `http://127.0.0.1:8000`

### 2. Environment Configuration
Verify or create `frontend/.env`:
```env
VITE_API_URL=http://127.0.0.1:8000
VITE_PAYPAL_CLIENT_ID=test
```

### 3. Start Development Server
```powershell
cd frontend
npm run dev
```
The application will launch at `http://localhost:5173`.

### 4. Build for Production
```powershell
cd frontend
npm run build
```
Generates optimized static assets in `frontend/dist/`.

---

## 🏗️ Architecture & Component Hierarchy

```
frontend/
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
├── .env.example
└── src/
    ├── main.jsx                 # Application entry point
    ├── App.jsx                  # Main router and global layout
    ├── index.css                # Tailwind directives & typography
    ├── api/
    │   ├── client.js            # Centralized fetch wrapper with 401 token revocation
    │   ├── auth.js              # Register, login, profile, server-side logout
    │   ├── products.js          # Product search, filters, offer comparisons
    │   ├── recommendations.js   # Deterministic AI recommendation engine
    │   ├── orders.js            # Server order creation & PayPal Sandbox capture
    │   └── admin.js             # Admin catalogue CRUD & status toggles
    ├── context/
    │   └── AuthContext.jsx      # Global user session & permission state
    ├── components/
    │   ├── DemoBanner.jsx       # Persistent simulated demo disclosure banner
    │   ├── Navbar.jsx           # Responsive header with role badges
    │   ├── Footer.jsx           # Educational disclaimers & precision notes
    │   ├── ProductCard.jsx      # Catalogue card with lowest landed cost
    │   ├── OfferCard.jsx        # Landed cost breakdown (item + shipping = total)
    │   ├── PayPalCheckoutButton.jsx # PayPal Sandbox integration with duplicate protection
    │   ├── ProtectedRoute.jsx   # Route guard for authenticated users
    │   ├── AdminRoute.jsx       # Route guard for role="admin"
    │   ├── LoadingSpinner.jsx   # Reusable loading spinner
    │   └── Alert.jsx            # Reusable feedback alert notifications
    └── pages/
        ├── Home.jsx             # Hero, search, landed cost comparison highlights
        ├── Products.jsx         # Catalogue search, category/brand filters & sorting
        ├── ProductDetail.jsx    # Price comparison table & AI recommendation
        ├── Checkout.jsx         # Shipping entry & PayPal Sandbox checkout
        ├── Orders.jsx           # User order history with status pills
        ├── OrderDetail.jsx      # Order receipt with verified PayPal capture logs
        ├── Login.jsx            # Sign in with authenticated user credentials
        ├── Register.jsx         # Public user registration (role="user")
        ├── AdminDashboard.jsx   # Product/Offer CRUD & status toggles
        └── NotFound.jsx         # 404 handler
```

---

## 🔒 Security & Precision Principles

1. **Client Never Calculates Financials**: All landed costs, subtotals, and currency conversions are computed strictly on the FastAPI backend using integer paise. The frontend only formats and renders verified backend values.
2. **Server-Side Token Revocation**: Logout immediately contacts `POST /api/auth/logout` to add the token's unique `jti` to the database denylist. If any API endpoint returns HTTP 401, the client automatically wipes local tokens.
3. **Role-Based Guards**: Admin panels (`/admin`) and endpoints (`/api/admin/*`) are double-guarded by `AdminRoute` and FastAPI HTTP Bearer role validation.
4. **Hackathon Disclaimers**: A persistent top banner, footer notes, and receipt watermarks clearly identify that products, prices, and PayPal transactions are simulated demo records.
