from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.connection import engine


def check_database_connection(db: Session | None = None) -> bool:
    """Return whether the configured database accepts a simple connection."""
    if db is not None:
        db.execute(text("SELECT 1 FROM DUAL"))
        return True

    with engine.connect() as connection:
        connection.execute(text("SELECT 1 FROM DUAL"))
    return True
