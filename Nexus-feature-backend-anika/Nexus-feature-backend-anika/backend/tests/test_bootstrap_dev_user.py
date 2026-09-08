import contextlib
import io
import os
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.database.base import Base
from app.models.case import Case
from app.models.user import User, UserRole
from scripts.bootstrap_dev_user import (
    BootstrapError,
    create_bootstrap_user,
    ensure_development_bootstrap_allowed,
    verify_bootstrap_password,
)


class BootstrapUserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session = Session(self.engine)

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def create_user(self, **overrides) -> User:
        values = {
            "username": "existing",
            "email": "existing@example.com",
            "password_hash": "existing-hash",
            "role": UserRole.ADMIN,
            "is_active": True,
        }
        values.update(overrides)
        user = User(**values)
        self.session.add(user)
        self.session.commit()
        return user

    def test_successful_admin_creation_and_hash(self) -> None:
        result = create_bootstrap_user(
            self.session,
            username="dev-admin",
            email="Dev.Admin@example.com",
            password="a-strong-development-password",
            full_name="Development Admin",
        )
        user = self.session.get(User, result.user_id)
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "dev-admin")
        self.assertEqual(user.email, "dev.admin@example.com")
        self.assertEqual(user.role, UserRole.ADMIN)
        self.assertTrue(user.is_active)
        self.assertNotEqual(user.password_hash, "a-strong-development-password")
        self.assertTrue(verify_bootstrap_password("a-strong-development-password", user.password_hash))
        self.assertFalse(verify_bootstrap_password("wrong-password", user.password_hash))
        self.assertEqual(self.session.scalar(select(User.id)).__class__, int)
        self.assertEqual(self.session.scalar(select(Case.id)), None)

    def test_duplicate_username_is_rejected(self) -> None:
        self.create_user(username="dev-admin", email="other@example.com")
        with self.assertRaisesRegex(BootstrapError, "username already exists"):
            create_bootstrap_user(self.session, username="dev-admin", email="new@example.com", password="a-strong-development-password")
        self.assertEqual(self.session.query(User).count(), 1)

    def test_duplicate_email_is_rejected(self) -> None:
        self.create_user(username="other", email="dev-admin@example.com")
        with self.assertRaisesRegex(BootstrapError, "email already exists"):
            create_bootstrap_user(self.session, username="dev-admin", email="DEV-ADMIN@example.com", password="a-strong-development-password")
        self.assertEqual(self.session.query(User).count(), 1)

    def test_weak_or_empty_password_is_rejected(self) -> None:
        for password in ("", "short", "            ", "dev-admin-password"):
            with self.subTest(password=password):
                with self.assertRaises(BootstrapError):
                    create_bootstrap_user(self.session, username="dev-admin", email="dev-admin@example.com", password=password)

    def test_refuses_without_development_environment(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(BootstrapError, "NEXUS_ENV=development"):
                ensure_development_bootstrap_allowed(True)

    def test_refuses_without_explicit_flag(self) -> None:
        with patch.dict(os.environ, {"NEXUS_ENV": "development"}, clear=True):
            with self.assertRaisesRegex(BootstrapError, "--allow-development-bootstrap"):
                ensure_development_bootstrap_allowed(False)

    def test_refuses_when_any_user_exists(self) -> None:
        self.create_user()
        with self.assertRaisesRegex(BootstrapError, "empty users table"):
            create_bootstrap_user(self.session, username="new", email="new@example.com", password="a-strong-development-password")
        self.assertEqual(self.session.query(User).count(), 1)

    def test_transaction_rolls_back_on_flush_failure(self) -> None:
        with patch.object(self.session, "flush", side_effect=RuntimeError("forced failure")):
            with self.assertRaises(RuntimeError):
                create_bootstrap_user(self.session, username="dev-admin", email="dev-admin@example.com", password="a-strong-development-password")
        self.session.rollback()
        self.assertEqual(self.session.query(User).count(), 0)

    def test_no_password_or_hash_is_printed(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = create_bootstrap_user(self.session, username="dev-admin", email="dev-admin@example.com", password="a-strong-development-password")
            print(f"Created development ADMIN user id={result.user_id} username={result.username}")
        rendered = output.getvalue()
        self.assertNotIn("a-strong-development-password", rendered)
        self.assertNotIn("$argon2", rendered)


if __name__ == "__main__":
    unittest.main()