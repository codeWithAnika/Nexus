import os
from collections.abc import Generator
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.base import Base

load_dotenv()


def _database_url() -> str:
    configured_url = os.getenv("DATABASE_URL")
    if configured_url:
        return configured_url

    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "1521")
    service_name = os.getenv("DB_SERVICE_NAME", "XEPDB1")
    username = quote_plus(os.getenv("DB_USERNAME", "NEXUS"))
    password = quote_plus(os.getenv("DB_PASSWORD", ""))
    return f"oracle+oracledb://{username}:{password}@{host}:{port}/?service_name={service_name}"


engine = create_engine(_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()