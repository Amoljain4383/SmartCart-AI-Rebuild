"""User authentication router: Registration, login, profile, and logout."""
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import (
    hash_password,
    verify_password,
    needs_rehash,
    create_access_token,
    decode_access_token,
)
from app.api.deps import get_current_user, security_scheme
from app.models.user import User
from app.models.revoked_token import RevokedToken
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
    MessageResponse,
)

router = APIRouter(prefix="", tags=["Authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account"
)
def register(
    request: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """Register a new standard user account.

    Public registration ALWAYS provisions normal 'user' privileges.
    Any attempt to supply administrative flags is completely ignored.
    """
    email_clean = request.email.strip().lower()

    # Enforce email uniqueness
    existing_user = db.query(User).filter(User.email == email_clean).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists."
        )

    # Provision standard user with Argon2id password hash
    new_user = User(
        email=email_clean,
        hashed_password=hash_password(request.password),
        full_name=request.full_name.strip(),
        role="user",  # Public registration is strictly restricted to 'user'
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generate JWT bearer access token
    access_token = create_access_token(subject=new_user.id, role=new_user.role)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(new_user)
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and receive JWT token"
)
def login(
    request: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """Authenticate with email and password to receive a JWT access token."""
    email_clean = request.email.strip().lower()

    user = db.query(User).filter(User.email == email_clean).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    # Inactive account verification
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive."
        )

    # Verify password against stored Argon2id hash
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    # Check if hash needs upgrading due to parameter evolution
    if needs_rehash(user.hashed_password):
        user.hashed_password = hash_password(request.password)
        db.commit()

    access_token = create_access_token(subject=user.id, role=user.role)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Retrieve current authenticated user profile"
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Return the profile of the currently authenticated user.

    Never exposes password hashes or secret tokens.
    """
    return UserResponse.model_validate(current_user)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Log out and invalidate current JWT access token"
)
def logout(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    """Logout endpoint that revokes the active token by persisting its jti to the denylist.

    Subsequent requests using this exact token will be rejected with HTTP 401.
    Repeated logout requests for an already revoked token are handled safely and idempotently.
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    jti = payload.get("jti")
    exp_timestamp = payload.get("exp")

    if jti and exp_timestamp:
        # Check if already revoked to handle repeated logout gracefully
        already_revoked = db.query(RevokedToken).filter(RevokedToken.jti == jti).first()
        if not already_revoked:
            expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            revoked_entry = RevokedToken(
                jti=jti,
                expires_at=expires_at
            )
            db.add(revoked_entry)
            db.commit()

    return MessageResponse(message="Successfully logged out.")
