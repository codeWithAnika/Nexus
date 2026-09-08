from __future__ import annotations

import argparse
import getpass
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pwdlib import PasswordHash
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models.user import User, UserRole


MIN_PASSWORD_LENGTH = 12
_EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
password_hash = PasswordHash.recommended()


class BootstrapError(ValueError):
    pass


@dataclass(frozen=True)
class BootstrapUserResult:
    user_id: int
    username: str
    email: str
    role: UserRole


def validate_bootstrap_credentials(username: str, email: str, password: str) -> tuple[str, str]:
    normalized_username = username.strip()
    normalized_email = email.strip().lower()
    if not normalized_username or len(normalized_username) > 100:
        raise BootstrapError("username is required and must be at most 100 characters")
    if not normalized_email or len(normalized_email) > 255 or not _EMAIL_PATTERN.fullmatch(normalized_email):
        raise BootstrapError("email is required and must be a valid email address")
    if not password or len(password) < MIN_PASSWORD_LENGTH or not password.strip():
        raise BootstrapError(f"password must be at least {MIN_PASSWORD_LENGTH} characters")
    if normalized_username.casefold() in password.casefold() or normalized_email.casefold() in password.casefold():
        raise BootstrapError("password must not contain the username or email")
    return normalized_username, normalized_email


def hash_bootstrap_password(password: str) -> str:
    return password_hash.hash(password)


def verify_bootstrap_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_bootstrap_user(
    session: Session,
    *,
    username: str,
    email: str,
    password: str,
    full_name: str | None = None,
) -> BootstrapUserResult:
    normalized_username, normalized_email = validate_bootstrap_credentials(username, email, password)
    try:
        with session.begin():
            duplicate_username = session.scalar(
                select(User.id).where(func.lower(User.username) == normalized_username.casefold())
            )
            if duplicate_username is not None:
                raise BootstrapError("username already exists")
            duplicate_email = session.scalar(
                select(User.id).where(func.lower(User.email) == normalized_email)
            )
            if duplicate_email is not None:
                raise BootstrapError("email already exists")
            if session.scalar(select(func.count(User.id))) != 0:
                raise BootstrapError("development bootstrap requires an empty users table")

            user = User(
                username=normalized_username,
                email=normalized_email,
                password_hash=hash_bootstrap_password(password),
                full_name=full_name.strip() if full_name and full_name.strip() else None,
                role=UserRole.ADMIN,
                is_active=True,
            )
            session.add(user)
            session.flush()
            result = BootstrapUserResult(user.id, user.username, user.email, user.role)
        return result
    except BootstrapError:
        raise
    except IntegrityError as exc:
        raise BootstrapError("user creation violated a database constraint") from exc


def ensure_development_bootstrap_allowed(allow_flag: bool) -> None:
    if os.getenv("NEXUS_ENV", "").strip().lower() != "development":
        raise BootstrapError("development bootstrap requires NEXUS_ENV=development")
    if not allow_flag:
        raise BootstrapError("development bootstrap requires --allow-development-bootstrap")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create the first Nexus development ADMIN user")
    parser.add_argument("--allow-development-bootstrap", action="store_true")
    args = parser.parse_args()
    try:
        ensure_development_bootstrap_allowed(args.allow_development_bootstrap)
        username = os.getenv("NEXUS_BOOTSTRAP_USERNAME", "")
        email = os.getenv("NEXUS_BOOTSTRAP_EMAIL", "")
        password = getpass.getpass("Bootstrap password: ")
        confirmation = getpass.getpass("Confirm bootstrap password: ")
        if password != confirmation:
            raise BootstrapError("passwords do not match")
        with SessionLocal() as session:
            result = create_bootstrap_user(
                session,
                username=username,
                email=email,
                password=password,
                full_name=os.getenv("NEXUS_BOOTSTRAP_FULL_NAME"),
            )
        print(f"Created development ADMIN user id={result.user_id} username={result.username} email={result.email}")
        return 0
    except BootstrapError as exc:
        print(f"Bootstrap refused: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())