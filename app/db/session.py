"""Database Engine and Session Management."""

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# Engine configuration depending on DB dialect
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL, connect_args=connect_args, pool_pre_ping=True, echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency for providing a transactional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
