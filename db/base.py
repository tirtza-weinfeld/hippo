"""Database configuration and session management.

This module provides the base SQLAlchemy setup for the dictionary database.
Uses SQLAlchemy 2.0 with async support and Neon PostgreSQL.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

if TYPE_CHECKING:
    from collections.abc import Generator

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL is None:
    msg = "DATABASE_URL environment variable must be set"
    raise ValueError(msg)

# Create engine with connection pooling
# pool_pre_ping ensures connections are alive before using them
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False,  # Set to True for SQL query logging
)

# Session factory for creating database sessions
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""


def get_db() -> Generator[Session]:
    """Dependency for FastAPI routes to get a database session.

    Yields:
        Session: A SQLAlchemy database session.

    Example:
        @router.get("/words")
        def get_words(db: Session = Depends(get_db)):
            return db.query(Word).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
