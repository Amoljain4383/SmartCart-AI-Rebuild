"""Comprehensive tests for Phase 2: Authentication & Admin Security."""
from datetime import timedelta
import pytest
from app.core.security import hash_password, create_access_token
from app.models.user import User


# 1. Successful user registration
def test_successful_user_registration(api_client):
    payload = {
        "email": "NewUser@SmartCart.IO",  # Mixed case to test normalization
        "password": "StrongPassword123!",
        "full_name": "New Shopper"
    }
    response = api_client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    user_info = data["user"]
    assert user_info["email"] == "newuser@smartcart.io"  # Lowercased
    assert user_info["full_name"] == "New Shopper"
    assert user_info["role"] == "user"
    assert user_info["is_active"] is True
    assert "password" not in user_info
    assert "hashed_password" not in user_info


# 2. Duplicate email registration rejection
def test_duplicate_email_registration_rejected(api_client):
    payload = {
        "email": "unique@example.com",
        "password": "Password123!",
        "full_name": "Original User"
    }
    resp1 = api_client.post("/api/auth/register", json=payload)
    assert resp1.status_code == 201

    # Second attempt with same email
    resp2 = api_client.post("/api/auth/register", json=payload)
    assert resp2.status_code == 400
    assert "already exists" in resp2.json()["detail"].lower()


# 3. Successful login
def test_successful_login(api_client, db_session):
    user = User(
        email="login_user@example.com",
        hashed_password=hash_password("LoginPass123!"),
        full_name="Login Test User",
        role="user",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()

    login_payload = {
        "email": "Login_User@example.com",
        "password": "LoginPass123!"
    }
    response = api_client.post("/api/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "login_user@example.com"


# 4. Incorrect password rejection
def test_incorrect_password_rejected(api_client, db_session):
    user = User(
        email="pass_test@example.com",
        hashed_password=hash_password("RealPassword123!"),
        full_name="Password Test",
        role="user",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()

    response = api_client.post("/api/auth/login", json={
        "email": "pass_test@example.com",
        "password": "WrongPassword999!"
    })
    assert response.status_code == 401
    assert "invalid email or password" in response.json()["detail"].lower()


# 5. Inactive user login rejection
def test_inactive_user_login_rejected(api_client, db_session):
    user = User(
        email="inactive@example.com",
        hashed_password=hash_password("ActivePass123!"),
        full_name="Inactive User",
        role="user",
        is_active=False  # Deactivated account
    )
    db_session.add(user)
    db_session.commit()

    response = api_client.post("/api/auth/login", json={
        "email": "inactive@example.com",
        "password": "ActivePass123!"
    })
    assert response.status_code == 401
    assert "inactive" in response.json()["detail"].lower()


# 6. Access to /api/auth/me with valid token
def test_get_current_user_profile(api_client, db_session):
    user = User(
        email="profile_check@example.com",
        hashed_password=hash_password("SecurePass123!"),
        full_name="Profile Checker",
        role="user",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token(subject=user.id, role=user.role)
    response = api_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user.id
    assert data["email"] == "profile_check@example.com"
    assert data["full_name"] == "Profile Checker"
    assert data["role"] == "user"
    assert "hashed_password" not in data


# 7. Unauthenticated access rejection
def test_unauthenticated_access_rejected(api_client):
    # Missing authorization header
    resp1 = api_client.get("/api/auth/me")
    assert resp1.status_code == 401

    resp2 = api_client.get("/api/admin/dashboard")
    assert resp2.status_code == 401


# 8. Normal user denied access to /api/admin/dashboard (HTTP 403)
def test_normal_user_denied_admin_dashboard(api_client, db_session):
    normal_user = User(
        email="regular_buyer@example.com",
        hashed_password=hash_password("UserPass123!"),
        full_name="Regular Buyer",
        role="user",
        is_active=True
    )
    db_session.add(normal_user)
    db_session.commit()

    user_token = create_access_token(subject=normal_user.id, role="user")
    response = api_client.get(
        "/api/admin/dashboard",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403
    assert "administrative privileges required" in response.json()["detail"].lower()


# 9. Admin allowed access to /api/admin/dashboard (HTTP 200)
def test_admin_allowed_access_to_dashboard(api_client, db_session):
    admin_user = User(
        email="site_admin@example.com",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Master Administrator",
        role="admin",
        is_active=True
    )
    db_session.add(admin_user)
    db_session.commit()

    admin_token = create_access_token(subject=admin_user.id, role="admin")
    response = api_client.get(
        "/api/admin/dashboard",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "access granted" in data["message"].lower()
    assert data["admin"]["role"] == "admin"
    assert data["admin"]["email"] == "site_admin@example.com"
    assert "hashed_password" not in data["admin"]


# 10. Attempted public admin registration safely creates ONLY normal user
def test_attempted_public_admin_registration(api_client, db_session):
    # Attacker tries to inject administrative fields
    exploit_payload = {
        "email": "hacker@example.com",
        "password": "SecretPass123!",
        "full_name": "Wannabe Admin",
        "role": "admin",
        "is_admin": True,
        "is_superuser": True
    }
    response = api_client.post("/api/auth/register", json=exploit_payload)
    assert response.status_code == 201
    data = response.json()

    # API returns user role
    assert data["user"]["role"] == "user"

    # Database state confirms user role
    db_user = db_session.query(User).filter(User.email == "hacker@example.com").first()
    assert db_user is not None
    assert db_user.role == "user"


# 11. Invalid and expired JWT rejection
def test_invalid_and_expired_jwt_rejected(api_client, db_session):
    user = User(
        email="tokencheck@example.com",
        hashed_password=hash_password("Pass1234!"),
        full_name="Token Check",
        role="user",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()

    # A: Corrupted / invalid signature token
    bad_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.payload"
    resp_bad = api_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {bad_token}"}
    )
    assert resp_bad.status_code == 401
    assert "invalid or expired" in resp_bad.json()["detail"].lower()

    # B: Expired token (-10 minutes)
    expired_token = create_access_token(
        subject=user.id,
        role=user.role,
        expires_delta=timedelta(minutes=-10)
    )
    resp_exp = api_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert resp_exp.status_code == 401
    assert "invalid or expired" in resp_exp.json()["detail"].lower()


# 12. Password hash never appears in API responses
def test_password_hash_never_exposed(api_client, db_session):
    register_payload = {
        "email": "safeuser@example.com",
        "password": "SafePassword123!",
        "full_name": "Privacy Advocate"
    }
    # Check registration response
    r1 = api_client.post("/api/auth/register", json=register_payload)
    assert "hash" not in str(r1.json()).lower()

    # Check login response
    r2 = api_client.post("/api/auth/login", json={
        "email": "safeuser@example.com",
        "password": "SafePassword123!"
    })
    token = r2.json()["access_token"]
    assert "hash" not in str(r2.json()).lower()

    # Check /me profile response
    r3 = api_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert "hash" not in str(r3.json()).lower()


# Logout test
def test_logout_endpoint(api_client, db_session):
    user = User(
        email="logout_user@example.com",
        hashed_password=hash_password("LogoutPass123!"),
        full_name="Logout User",
        role="user",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token(subject=user.id, role=user.role)
    response = api_client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert "successfully logged out" in response.json()["message"].lower()

    # Verify that the token is genuinely revoked
    r_me = api_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r_me.status_code == 401
    assert "revoked" in r_me.json()["detail"].lower()
