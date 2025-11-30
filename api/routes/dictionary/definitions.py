"""Definition endpoints for dictionary API.

Handles individual definition operations.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.services import definition_service
from db import get_db
from schemas.dictionary import DefinitionNested, DefinitionOut

router = APIRouter(tags=["definitions"])


@router.post(
    "/words/{word_id}/definitions", response_model=DefinitionOut, status_code=201
)
def create_definition(
    word_id: int,
    definition: DefinitionNested,
    db: Annotated[Session, Depends(get_db)],
) -> DefinitionOut:
    """Add a definition to an existing word."""
    return definition_service.create_definition(db, word_id, definition)


@router.get("/definitions/{definition_id}", response_model=DefinitionOut)
def get_definition(
    definition_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> DefinitionOut:
    """Get a specific definition."""
    return definition_service.get_definition(db, definition_id)


@router.patch("/definitions/{definition_id}", response_model=DefinitionOut)
def update_definition(
    definition_id: int,
    definition: DefinitionNested,
    db: Annotated[Session, Depends(get_db)],
) -> DefinitionOut:
    """Update a specific definition."""
    return definition_service.update_definition(db, definition_id, definition)


@router.delete("/definitions/{definition_id}", status_code=204, response_model=None)
def delete_definition(
    definition_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Delete a specific definition (cascades to examples)."""
    definition_service.delete_definition(db, definition_id)
