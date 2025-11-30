"""Example endpoints for dictionary API.

Handles individual example operations.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.services import example_service
from db import get_db
from schemas.dictionary import ExampleBase, ExampleOut

router = APIRouter(tags=["examples"])


@router.post(
    "/definitions/{definition_id}/examples", response_model=ExampleOut, status_code=201
)
def create_example(
    definition_id: int,
    example: ExampleBase,
    db: Annotated[Session, Depends(get_db)],
) -> ExampleOut:
    """Add an example to an existing definition."""
    return example_service.create_example(db, definition_id, example)


@router.get("/examples/{example_id}", response_model=ExampleOut)
def get_example(
    example_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> ExampleOut:
    """Get a specific example."""
    return example_service.get_example(db, example_id)


@router.patch("/examples/{example_id}", response_model=ExampleOut)
def update_example(
    example_id: int,
    example: ExampleBase,
    db: Annotated[Session, Depends(get_db)],
) -> ExampleOut:
    """Update a specific example."""
    return example_service.update_example(db, example_id, example)


@router.delete("/examples/{example_id}", status_code=204, response_model=None)
def delete_example(
    example_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Delete a specific example."""
    example_service.delete_example(db, example_id)
