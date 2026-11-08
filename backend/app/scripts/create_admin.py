"""Protected Admin Provisioning CLI.

Admin accounts can NEVER be created through public HTTP registration.
This script provisions an administrator directly into the database using Argon2id.

Usage:
    python -m app.scripts.create_admin --email admin@example.com --password "SecurePass123!" --name "Site Admin"

If arguments are omitted, values are loaded from environment variables (ADMIN_INITIAL_EMAIL, etc.)
or requested via interactive prompt.
"""
import argparse
import sys
from typing import Optional
from getpass import getpass
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.core.config import settings
from app.models.user import User


def provision_admin(
    email: str,
    password: str,
    full_name: str,
    db: Optional[Session] = None
) -> bool:
    """Create or elevate an admin user safely in the database.

    Returns True on success, False if already exists or invalid.
    """
    email = email.strip().lower()
    if not email or "@" not in email:
        print("[ERROR] Invalid email address provided.")
        return False

    if len(password) < 8:
        print("[ERROR] Password must be at least 8 characters long.")
        return False

    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            if existing_user.role == "admin":
                print(f"[INFO] User '{email}' already exists and is already an administrator.")
                return True
            else:
                existing_user.role = "admin"
                existing_user.hashed_password = hash_password(password)
                if full_name:
                    existing_user.full_name = full_name
                db.commit()
                print(f"[SUCCESS] Existing user '{email}' was elevated to administrator.")
                return True

        new_admin = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name or "System Administrator",
            role="admin",
            is_active=True
        )
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)
        print(f"[SUCCESS] Admin account created successfully for '{email}' (ID: {new_admin.id}).")
        return True
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to provision admin: {e}")
        return False
    finally:
        if close_db:
            db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Protected Admin Provisioning CLI for SmartCart AI (passwords are entered securely via getpass)"
    )
    parser.add_argument("--email", help="Administrator email address")
    parser.add_argument("--name", help="Administrator full name")
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run without prompts; reads password strictly from ADMIN_INITIAL_PASSWORD environment variable"
    )

    args = parser.parse_args()

    email = args.email or settings.ADMIN_INITIAL_EMAIL
    name = args.name or settings.ADMIN_INITIAL_NAME

    if not email and not args.non_interactive:
        email = input("Admin email: ").strip()

    if args.non_interactive:
        password = settings.ADMIN_INITIAL_PASSWORD
    else:
        # Secure interactive password entry without shell command-line history exposure
        password = getpass("Admin password: ").strip()
        if not password:
            print("[ERROR] Password cannot be empty.")
            sys.exit(1)
        confirm = getpass("Confirm admin password: ").strip()
        if password != confirm:
            print("[ERROR] Passwords do not match.")
            sys.exit(1)

    if not name and not args.non-interactive:
        name = input("Admin full name [System Administrator]: ").strip() or "System Administrator"

    if not email or not password:
        print("[ERROR] Both email and password are required to create an admin account.")
        sys.exit(1)

    success = provision_admin(email=email, password=password, full_name=name)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
