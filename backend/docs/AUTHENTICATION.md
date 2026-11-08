# SmartCart AI — Authentication & Security Guide

## 1. Overview
SmartCart AI uses state-of-the-art **Argon2id** password hashing and **JWT Bearer Token** authentication coupled with Role-Based Access Control (RBAC). 

- Standard users receive the `user` role upon registration.
- Administrator privileges (`admin` role) can **never** be obtained through public registration.
- Monetary data is processed strictly in integer paise (INR).

---

## 2. Authentication Flow

### 2.1 User Registration (`POST /api/auth/register`)
- Accepts `email`, `password`, and `full_name`.
- Automatically lowercases and validates email syntax.
- Enforces password length of at least 8 non-whitespace characters.
- Generates a salted **Argon2id** hash using `time_cost=2`, `memory_cost=102400` (100 MiB), and `parallelism=8`.
- Strictly hardcodes `role = "user"`. Any submitted payload containing administrative parameters (e.g. `role: "admin"` or `is_admin: true`) is ignored.
- Returns HTTP 201 with a signed JWT access token and user profile.

### 2.2 User Login (`POST /api/auth/login`)
- Verifies credentials against the stored Argon2id hash.
- Rejects deactivated accounts (`is_active == False`) with HTTP 401.
- Automatically handles hash parameter upgrades via `needs_rehash()`.
- Issues a signed JWT access token containing user identity and role.

### 2.3 User Profile (`GET /api/auth/me`)
- Protected route requiring an `Authorization: Bearer <token>` header.
- Decodes token, validates expiration and signature against server `SECRET_KEY`.
- Returns the current user profile. **Password hashes are never included.**

### 2.4 User Logout & Token Revocation (`POST /api/auth/logout`)
- Every JWT access token is issued with a unique UUID4 `jti` (JWT ID) and an explicit `"type": "access"` claim.
- Calling `POST /api/auth/logout` extracts the token's `jti` and its expiration timestamp (`exp`).
- The `jti` is persisted into the `revoked_tokens` database denylist table.
- Subsequent requests attempting to use the revoked token are immediately rejected with `HTTP 401 Unauthorized ("Token has been revoked.")`.
- **Multi-device session isolation**: Revoking one token on device A does not invalidate active sessions on device B because each token possesses a unique `jti`.
- **Idempotency**: Repeated logout requests with an already-revoked token are handled safely and return `200 OK`.
- **Safe pruning**: Expired denylist records can be purged via `app.db.revocation_cleanup.cleanup_expired_revoked_tokens(db)` without compromising security.

---

## 3. Admin Security & RBAC Protection

### 3.1 Protected Admin Endpoint (`GET /api/admin/dashboard`)
- Guarded by the `get_current_admin_user` dependency.
- **Unauthenticated requests** receive `HTTP 401 Unauthorized`.
- **Standard users** (`role == "user"`) receive `HTTP 403 Forbidden`.
- **Administrators** (`role == "admin"`) receive `HTTP 200 OK` with safe admin metadata.

### 3.2 Secure Out-of-Band Admin Provisioning
Admin accounts can **only** be created or elevated through the CLI utility:

```powershell
cd backend
..\.venv\Scripts\python.exe -m app.scripts.create_admin --email admin@smartcart.local
```
- **Hidden Password Prompt**: Uses `getpass.getpass()` with confirmation to prevent passwords from leaking into shell command history.
- **Non-Interactive CI Mode**: In containerized or automated pipelines, pass `--non-interactive` to read the password directly from the `ADMIN_INITIAL_PASSWORD` environment variable.

---

## 4. Environment Variables

All settings are configured via `backend/.env` (modeled after `backend/.env.example`):

| Variable | Default (Dev) | Description |
| :--- | :--- | :--- |
| `SECRET_KEY` | *(dev placeholder)* | 64-char random secret for HMAC-SHA256 JWT signing |
| `ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Token validity lifetime in minutes |
| `DATABASE_URL` | `sqlite:///./smartcart.db` | Database URL (SQLite dev / PostgreSQL prod) |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Whitelisted origins |
| `ADMIN_INITIAL_EMAIL` | `admin@smartcart.local` | Default bootstrap admin email for CLI |
| `ADMIN_INITIAL_PASSWORD` | `ChangeMeAdmin123!` | Default bootstrap admin password for CLI |

---

## 5. Running Automated Tests

Run the full test suite using `pytest`:

```powershell
cd backend
..\.venv\Scripts\pytest.exe -v
```

All 27 automated tests run against an in-memory SQLite database, leaving the development database (`smartcart.db`) untouched.
