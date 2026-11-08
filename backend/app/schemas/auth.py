"""Authentication and authorization schemas."""
import re
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class UserRegisterRequest(BaseModel):
    """Public user registration payload.

    Strictly ignores or rejects any attempt to pass 'role' or administrative flags.
    Public registration will ALWAYS create an account with role='user'.
    """
    model_config = ConfigDict(extra="ignore")

    email: str = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password (min 8 characters)")
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name of user")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        clean = v.strip().lower()
        if not clean or not EMAIL_REGEX.match(clean):
            raise ValueError("Invalid email address format.")
        return clean

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        trimmed = v.strip()
        if len(trimmed) < 8:
            raise ValueError("Password must be at least 8 non-whitespace characters long.")
        return trimmed

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        trimmed = v.strip()
        if len(trimmed) < 2:
            raise ValueError("Full name must be at least 2 characters long.")
        return trimmed


class UserLoginRequest(BaseModel):
    """User credentials for obtaining JWT access token."""
    email: str = Field(..., description="Registered email address")
    password: str = Field(..., description="Account password")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UserResponse(BaseModel):
    """Safe public user representation. Never contains password hashes or secrets."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    """Bearer access token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class MessageResponse(BaseModel):
    """Simple status confirmation response."""
    message: str


class AdminDashboardResponse(BaseModel):
    """Safe admin dashboard status response."""
    status: str = "success"
    message: str
    admin: Dict[str, Any]
