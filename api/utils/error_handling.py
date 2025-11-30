"""Centralized error handling utilities."""

from __future__ import annotations

from typing import NoReturn

from fastapi import HTTPException
from sqlalchemy.orm import Session

from api.utils.logger import logger


def handle_db_error(
    operation: str,
    status_code: int = 500,
    *,
    db: Session | None = None,
) -> NoReturn:
    """Handle database errors with logging and rollback.

    Args:
        operation: Description of the operation that failed (e.g., "create word")
        status_code: HTTP status code to return (default: 500)
        db: Database session to rollback (optional)

    Raises:
        HTTPException: Always raises with the given status code
    """
    if db is not None:
        db.rollback()

    logger.exception("Failed to %s", operation)
    raise HTTPException(
        status_code=status_code,
        detail=f"Failed to {operation}",
    ) from None
