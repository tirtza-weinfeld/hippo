"""Word relation endpoints for dictionary API.

Handles synonyms, antonyms, etc.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.services import relation_service
from db import get_db
from schemas.dictionary import PaginatedRelations, RelationCreate, RelationOut

router = APIRouter(prefix="/relations", tags=["relations"])


@router.post("", response_model=RelationOut, status_code=201)
def create_relation(
    relation: RelationCreate,
    db: Annotated[Session, Depends(get_db)],
) -> RelationOut:
    """Create a word relation (synonym, antonym, etc)."""
    return relation_service.create_relation(db, relation)


@router.get("", response_model=PaginatedRelations)
def list_relations(
    db: Annotated[Session, Depends(get_db)],
    word_id: Annotated[int | None, Query(description="Filter by word ID")] = None,
    relation_type: Annotated[
        str | None, Query(description="Filter by relation type")
    ] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> PaginatedRelations:
    """List word relations."""
    return relation_service.list_relations(db, word_id, relation_type, page, page_size)


@router.delete(
    "/{word_id_1}/{word_id_2}/{relation_type}", status_code=204, response_model=None
)
def delete_relation(
    word_id_1: int,
    word_id_2: int,
    relation_type: str,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Delete a word relation.

    Args:
        word_id_1: First word ID
        word_id_2: Second word ID
        relation_type: Type of relation (synonym, antonym, etc.)
        db: Database session
    """
    relation_service.delete_relation(db, word_id_1, word_id_2, relation_type)
