import os
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database.base import Base
from app.database import connection
from app.main import readiness_check
from scripts import bootstrap_demo


class LocalEnvironmentTests(unittest.TestCase):
    def test_ready_reports_database_reachable(self) -> None:
        with patch("app.main.database_ready", return_value=True):
            self.assertEqual(readiness_check(), {"status": "ready"})

    def test_ready_reports_database_unavailable_without_details(self) -> None:
        with patch("app.main.database_ready", return_value=False):
            response = readiness_check()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.body, b'{"status":"not_ready"}')

    def test_bootstrap_demo_is_idempotent(self) -> None:
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        with Session(engine) as session:
            first = bootstrap_demo.bootstrap_demo(
                session,
                username="nexus-admin",
                email="admin@nexus.local",
                password="local-development-password",
            )
            second = bootstrap_demo.bootstrap_demo(
                session,
                username="nexus-admin",
                email="admin@nexus.local",
                password="local-development-password",
            )
            self.assertTrue(first.user_created)
            self.assertTrue(first.case_created)
            self.assertFalse(second.user_created)
            self.assertFalse(second.case_created)
            self.assertEqual(first.user_id, second.user_id)
            self.assertEqual(first.case_id, second.case_id)
        engine.dispose()

    def test_sqlite_requires_development_environment(self) -> None:
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///./nexus_demo.db", "NEXUS_ENV": "production"}):
            with self.assertRaisesRegex(RuntimeError, "NEXUS_ENV=development"):
                connection._database_url()


if __name__ == "__main__":
    unittest.main()