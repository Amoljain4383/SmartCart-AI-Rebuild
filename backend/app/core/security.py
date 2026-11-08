"""Security utilities: Argon2id password hashing and JWT token management."""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from app.core.config import settings

# Argon2id reference password hasher with secure parameters
_ph = PasswordHasher(
    time_cost=2,         # 2 iterations
    memory_cost=102400,  # 100 MiB memory usage (resists ASIC/GPU attacks)
    parallelism=8,       # 8 parallel threads
    hash_len=32,
    salt_len=16
)


def hash_password(password: str) -> str:
    """Hash a plaintext password using Argon2id."""
    return _ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against an Argon2id hash."""
    try:
        return _ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(hashed_password: str) -> bool:
    """Check if the hash needs an upgrade due to changed cost parameters."""
    return _ph.check_needs_rehash(hashed_password)


def create_access_token(
    subject: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
    custom_jti: Optional[str] = None
) -> str:
    """Generate a signed JWT bearer token containing user ID (sub), role, type, and unique jti."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    jti = custom_jti or str(uuid.uuid4())

    to_encode: Dict[str, Any] = {
        "sub": subject,
        "role": role,
        "type": "access",
        "jti": jti,
        "iat": now,
        "exp": expire,
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT bearer token.

    Validates signature, expiration, configured algorithm, token type ('access'), and presence of 'jti'.
    Returns payload dict or None if invalid.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # Enforce token type
        if payload.get("type") != "access":
            return None
        # Enforce valid non-empty jti
        jti = payload.get("jti")
        if not jti or not isinstance(jti, str) or len(jti.strip()) == 0:
            return None
        return payload
    except (jwt.PyJWTError, ValueError):
        return None
