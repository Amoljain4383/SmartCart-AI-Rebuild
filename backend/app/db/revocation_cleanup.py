"""Maintenance utility to safely purge expired revoked token records."""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.revoked_token import RevokedToken


def cleanup_expired_revoked_tokens(db: Session) -> int:
    """Delete expired revoked token records.

    Safe:
    - Only deletes records where `expires_at < now`.
    - Unexpired revocation records are strictly preserved.
    - Since tokens past their expiration are independently rejected by jwt.decode,
      pruning them from the denylist keeps the table compact without any security loss.

    Returns:
        int: Number of pruned records.
    """
    now = datetime.now(timezone.utc)
    deleted_count = db.query(RevokedToken).filter(RevokedToken.expires_at < now).delete(synchronize_session=False)
    db.commit()
    return deleted_count
