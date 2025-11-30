"""Tag endpoints for dictionary API.

Thin route handlers - business logic in services.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.services import tag_service
from db import get_db
from schemas.dictionary import PaginatedTags, TagCreate, TagOut, TagUpdate

router = APIRouter(prefix="/tags", tags=["tags"])


@router.post("", response_model=TagOut, status_code=201)
def create_tag(
    tag: TagCreate,
    db: Annotated[Session, Depends(get_db)],
) -> TagOut:
    """Create a new tag."""
    return tag_service.create_tag(db, tag)


@router.get("", response_model=PaginatedTags)
def list_tags(
    db: Annotated[Session, Depends(get_db)],
    search: Annotated[str | None, Query(description="Search tag name")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> PaginatedTags:
    """List or search tags."""
    return tag_service.list_tags(db, search, page, page_size)


@router.get("/{tag_id}", response_model=TagOut)
def get_tag(
    tag_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> TagOut:
    """Get a specific tag."""
    return tag_service.get_tag(db, tag_id)


@router.patch("/{tag_id}", response_model=TagOut)
def update_tag(
    tag_id: int,
    tag_update: TagUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> TagOut:
    """Update a tag."""
    return tag_service.update_tag(db, tag_id, tag_update)


@router.delete("/{tag_id}", status_code=204, response_model=None)
def delete_tag(
    tag_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Delete a tag."""
    tag_service.delete_tag(db, tag_id)
