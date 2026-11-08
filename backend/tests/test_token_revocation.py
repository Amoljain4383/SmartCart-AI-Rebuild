"""Dedicated automated tests for Solution A: JWT Revocation & Token Denylist."""
from datetime import datetime, timedelta, timezone
import jwt
import pytest
from app.core.config import settings
from app.core.security import hash_password, create_access_token, decode_access_token
from app.models.user import User
from app.models.revoked_token import RevokedToken
from app.db.revocation_cleanup import cleanup_expired_revoked_tokens


# 1. Newly issued token works
def test_newly_issued_token_works(api_client, db_session):
    user = User(
        email="fresh_token@test.com",
        hashed_password=hash_password("Pass1234!"),
        full_name="Fresh User",
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
    assert response.json()["email"] == "fresh_token@test.com"


# 2 & 3. Logging out revokes that exact token, preventing access to /api/auth/me
def test_logout_revokes_token_and_blocks_profile_access(api_client, db_session):
    user = User(
        email="revocation_user@test.com",
        hashed_password=hash_password("Pass1234!"),
        full_name="Revoke User",
        role="user",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token(subject=user.id, role=user.role)
    headers = {"Authorization": f"Bearer {token}"}

    # Before logout: access succeeds
    r_before = api_client.get("/api/auth/me", headers=headers)
    assert r_before.status_code == 200

    # Execute logout
    r_logout = api_client.post("/api/auth/logout", headers=headers)
    assert r_logout.status_code == 200
    assert "successfully logged out" in r_logout.json()["message"].lower()

    # After logout: exact same token is rejected
    r_after = api_client.get("/api/auth/me", headers=headers)
    assert r_after.status_code == 401
    assert "token has been revoked" in r_after.json()["detail"].lower()


# 4. Revoked token cannot access admin endpoints
def test_revoked_token_cannot_access_admin_endpoints(api_client, db_session):
    admin = User(
        email="revoked_admin@test.com",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Admin To Revoke",
        role="admin",
        is_active=True
    )
    db_session.add(admin)
    db_session.commit()

    admin_token = create_access_token(subject=admin.id, role="admin")
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Verify access granted before logout
    assert api_client.get("/api/admin/dashboard", headers=headers).status_code == 200

    # Logout
    api_client.post("/api/auth/logout", headers=headers)

    # Verify access is now rejected with 401
    r_admin_after = api_client.get("/api/admin/dashboard", headers=headers)
    assert r_admin_after.status_code == 401
    assert "token has been revoked" in r_admin_after.json()["detail"].lower()


# 5. Logging out one token does not revoke another valid token belonging to the same user
def test_multi_session_concurrency_isolated_revocation(api_client, db_session):
    user = User(
        email="multi_device@test.com",
        hashed_password=hash_password("MultiPass123!"),
        full_name="Multi Device User",
        role="user",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()

    # Device A token
    token_device_a = create_access_token(subject=user.id, role=user.role)
    # Device B token (unique jti)
    token_device_b = create_access_token(subject=user.id, role=user.role)

    # Logout Device A
    r_logout_a = api_client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {token_device_a}"}
    )
    assert r_logout_a.status_code == 200

    # Device A token is now revoked
    r_a = api_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_device_a}"})
    assert r_a.status_code == 401
    assert "token has been revoked" in r_a.json()["detail"].lower()

    # Device B token REMAINS completely valid!
    r_b = api_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_device_b}"})
    assert r_b.status_code == 200
    assert r_b.json()["email"] == "multi_device@test.com"


# 6. Repeated logout requests behave safely (idempotent)
def test_repeated_logout_safe_and_idempotent(api_client, db_session):
    user = User(
        email="idempotent_logout@test.com",
        hashed_password=hash_password("Pass1234!"),
        full_name="Idempotent Logout",
        role="user",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token(subject=user.id, role=user.role)
    headers = {"Authorization": f"Bearer {token}"}

    # 1st logout
    r1 = api_client.post("/api/auth/logout", headers=headers)
    assert r1.status_code == 200

    # 2nd logout with same token (already revoked)
    r2 = api_client.post("/api/auth/logout", headers=headers)
    assert r2.status_code == 200
    assert "successfully logged out" in r2.json()["message"].lower()


# 7. Tokens without jti are rejected
def test_tokens_without_jti_rejected(api_client, db_session):
    user = User(
        email="nojti@test.com",
        hashed_password=hash_password("Pass1234!"),
        full_name="No JTI",
        role="user",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()

    # Craft token missing jti
    payload_without_jti = {
        "sub": user.id,
        "role": user.role,
        "type": "access",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15)
    }
    raw_token = jwt.encode(payload_without_jti, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    response = api_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {raw_token}"}
    )
    assert response.status_code == 401
    assert "invalid or expired" in response.json()["detail"].lower()


# 8. Tokens with the wrong type are rejected
def test_tokens_with_wrong_type_rejected(api_client, db_session):
    user = User(
        email="wrongtype@test.com",
        hashed_password=hash_password("Pass1234!"),
        full_name="Wrong Type",
        role="user",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()

    # Craft token with type='refresh'
    payload_wrong_type = {
        "sub": user.id,
        "role": user.role,
        "type": "refresh",
        "jti": "sample-uuid-jti-123",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15)
    }
    raw_token = jwt.encode(payload_wrong_type, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    response = api_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {raw_token}"}
    )
    assert response.status_code == 401
    assert "invalid or expired" in response.json()["detail"].lower()


# 9. Cleanup function deletes only expired tokens and preserves unexpired tokens
def test_cleanup_expired_revoked_tokens(db_session):
    now = datetime.now(timezone.utc)

    # Expired token in denylist (expired 1 hour ago)
    expired_denylist = RevokedToken(
        jti="expired-jti-001",
        expires_at=now - timedelta(hours=1),
        created_at=now - timedelta(hours=2)
    )
    # Active unexpired token in denylist (expires in 1 hour)
    active_denylist = RevokedToken(
        jti="active-jti-002",
        expires_at=now + timedelta(hours=1),
        created_at=now
    )
    db_session.add_all([expired_denylist, active_denylist])
    db_session.commit()

    # Run cleanup
    pruned = cleanup_expired_revoked_tokens(db_session)
    assert pruned == 1

    # Verify active denylist record remains preserved
    assert db_session.query(RevokedToken).filter(RevokedToken.jti == "active-jti-002").first() is not None
    # Verify expired denylist record was deleted
    assert db_session.query(RevokedToken).filter(RevokedToken.jti == "expired-jti-001").first() is None
