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
DEFAULT_USERNAME = "nexus-admin"
DEFAULT_EMAIL = "admin@nexus.local"
DEFAULT_FULL_NAME = "Nexus Development Administrator"
DEMO_CASE_NUMBER = "OPERATION-NEXUS"
DEMO_CASE_TITLE = "Operation Nexus"
MIN_PASSWORD_LENGTH = 12
_EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
password_hash = PasswordHash.recommended()


class BootstrapError(ValueError):
    pass


@dataclass(frozen=True)
class BootstrapResult:
    user_id: int
    case_id: int
    user_created: bool
    case_created: bool


def ensure_development_environment() -> None:
    if os.getenv("NEXUS_ENV", "").strip().lower() != "development":
        raise BootstrapError("demo bootstrap requires NEXUS_ENV=development")


def validate_credentials(username: str, email: str, password: str) -> tuple[str, str]:
    username = username.strip()
    email = email.strip().lower()
    if not username or len(username) > 100:
        raise BootstrapError("username is required and must be at most 100 characters")
    if not _EMAIL_PATTERN.fullmatch(email) or len(email) > 255:
        raise BootstrapError("email must be a valid email address")
    if len(password) < MIN_PASSWORD_LENGTH or not password.strip():
        raise BootstrapError(f"password must be at least {MIN_PASSWORD_LENGTH} characters")
    return username, email


def bootstrap_demo(
    session,
    *,
    username: str,
    email: str,
    password: str,
    full_name: str = DEFAULT_FULL_NAME,
) -> BootstrapResult:
    from sqlalchemy import select
    from sqlalchemy.exc import IntegrityError

    from app.models.case import Case, CasePriority, CaseStatus
    from app.models.user import User, UserRole

    username, email = validate_credentials(username, email, password)
    try:
        with session.begin():
            user = session.scalar(select(User).where(User.username == username))
            if user is None:
                user = session.scalar(select(User).where(User.email == email))
            user_created = user is None
            if user is None:
                user = User(
                    username=username,
                    email=email,
                    password_hash=password_hash.hash(password),
                    full_name=full_name,
                    role=UserRole.ADMIN,
                    is_active=True,
                )
                session.add(user)
                session.flush()
            elif user.role != UserRole.ADMIN:
                raise BootstrapError("existing development user is not an ADMIN")

            case = session.scalar(select(Case).where(Case.case_number == DEMO_CASE_NUMBER))
            case_created = case is None
            if case is None:
                case = Case(
                    case_number=DEMO_CASE_NUMBER,
                    title=DEMO_CASE_TITLE,
                    description="Development demonstration case for the Nexus command centre.",
                    status=CaseStatus.OPEN,
                    priority=CasePriority.HIGH,
                    created_by=user.id,
                )
                session.add(case)
                session.flush()
            result = BootstrapResult(user.id, case.id, user_created, case_created)
        return result
    except BootstrapError:
        raise
    except IntegrityError as exc:
        raise BootstrapError("demo bootstrap violated a database constraint") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Create the local Nexus development user and demo case")
    parser.add_argument("--username", default=os.getenv("NEXUS_BOOTSTRAP_USERNAME", DEFAULT_USERNAME))
    parser.add_argument("--email", default=os.getenv("NEXUS_BOOTSTRAP_EMAIL", DEFAULT_EMAIL))
    parser.add_argument("--full-name", default=os.getenv("NEXUS_BOOTSTRAP_FULL_NAME", DEFAULT_FULL_NAME))
    args = parser.parse_args()
    try:
        ensure_development_environment()
        password = getpass.getpass("Development admin password: ")
        from app.database.connection import SessionLocal

        with SessionLocal() as session:
            result = bootstrap_demo(
                session,
                username=args.username,
                email=args.email,
                password=password,
                full_name=args.full_name,
            )
        print(f"Development user id={result.user_id} (created={result.user_created})")
        print(f"Operation Nexus case id={result.case_id} (created={result.case_created})")
        return 0
    except BootstrapError as exc:
        print(f"Bootstrap refused: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())