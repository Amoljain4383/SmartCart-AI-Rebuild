"""Database model for denylisted/revoked JWT tokens."""
from sqlalchemy import Column, String, DateTime
from app.core.database import Base
from app.models.base import utc_now


class RevokedToken(Base):
    """Denylisted JWT identifier (jti).

    Tracks revoked access tokens without persisting raw token strings or secrets.
    """
    __tablename__ = "revoked_tokens"

    jti = Column(String(36), primary_key=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    def __repr__(self) -> str:
        return f"<RevokedToken(jti='{self.jti}', expires_at='{self.expires_at}')>"
