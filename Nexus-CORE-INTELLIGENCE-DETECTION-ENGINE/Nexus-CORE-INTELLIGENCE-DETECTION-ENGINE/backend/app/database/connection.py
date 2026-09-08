import os
from collections.abc import Generator
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.database.base import Base

load_dotenv()


def _database_url() -> str:
    configured_url = os.getenv("DATABASE_URL")
    if configured_url:
        if configured_url.startswith("sqlite") and os.getenv("NEXUS_ENV", "production").strip().lower() != "development":
            raise RuntimeError("SQLite is supported only when NEXUS_ENV=development")
        return configured_url

    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "1521")
    service_name = os.getenv("DB_SERVICE_NAME", "XEPDB1")
    username = quote_plus(os.getenv("DB_USERNAME", "NEXUS"))
    password = quote_plus(os.getenv("DB_PASSWORD", ""))
    return f"oracle+oracledb://{username}:{password}@{host}:{port}/?service_name={service_name}"


_configured_database_url = _database_url()
_engine_options = {"pool_pre_ping": True}
if _configured_database_url.startswith("sqlite"):
    _engine_options["connect_args"] = {"check_same_thread": False}
engine = create_engine(_configured_database_url, **_engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def database_ready() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()