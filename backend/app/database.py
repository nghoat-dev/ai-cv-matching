"""
SQLAlchemy database configuration for AI CV-Job Matching backend.

Provides the engine, session factory, dependency-injection helper,
declarative base, and a table-creation utility.
"""

from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./cv_matching.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # required for SQLite
    echo=False,
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# ---------------------------------------------------------------------------
# Declarative base
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


# ---------------------------------------------------------------------------
# Dependency-injection helper
# ---------------------------------------------------------------------------


def get_db():
    """Yield a database session and guarantee proper cleanup.

    Usage (FastAPI)::

        @router.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db: Session = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Table creation
# ---------------------------------------------------------------------------


def create_tables() -> None:
    """Create all tables defined in the ORM models (idempotent)."""
    # Import models here to ensure they are registered with Base before
    # create_all() is called.
    from backend.app import models  # noqa: F401  (side-effect import)

    Base.metadata.create_all(bind=engine)
