"""Tag service - business logic for tag operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException

from api.utils import build_paginated_response, handle_db_error
from db.models.dictionary import Tag
from schemas.dictionary import PaginatedTags, TagCreate, TagOut, TagUpdate

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_or_create_tags(db: Session, tag_names: list[str]) -> list[int]:
    """Get or create tags by name, return list of tag IDs.

    Args:
        db: Database session
        tag_names: List of tag names

    Returns:
        List of tag IDs
    """
    if not tag_names:
        return []

    tag_ids: list[int] = []

    for tag_name in tag_names:
        # Try to find existing tag
        existing_tag = db.query(Tag).filter(Tag.name == tag_name).first()

        if existing_tag:
            tag_ids.append(existing_tag.id)
        else:
            # Create new tag
            new_tag = Tag(name=tag_name, description=None)
            db.add(new_tag)
            db.flush()  # Get the ID without committing
            tag_ids.append(new_tag.id)

    return tag_ids


def create_tag(db: Session, tag: TagCreate) -> TagOut:
    """Create a new tag."""
    try:
        # Check if tag already exists
        existing = db.query(Tag).filter(Tag.name == tag.name).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Tag '{tag.name}' already exists",
            )

        db_tag = Tag(name=tag.name, description=tag.description)
        db.add(db_tag)
        db.commit()
        db.refresh(db_tag)

        return TagOut.model_validate(db_tag)

    except HTTPException:
        raise
    except Exception:
        handle_db_error("create tag", db=db)


def list_tags(
    db: Session,
    search: str | None,
    page: int,
    page_size: int,
) -> PaginatedTags:
    """List or search tags with pagination."""
    try:
        query = db.query(Tag)

        # Apply search filter
        if search:
            query = query.filter(Tag.name.ilike(f"{search}%"))

        # Order by name
        query = query.order_by(Tag.name.asc())

        # Paginate
        total = query.count()
        skip = (page - 1) * page_size
        tags = query.offset(skip).limit(page_size).all()

        tag_outs = [TagOut.model_validate(t) for t in tags]
        return PaginatedTags.model_validate(
            build_paginated_response(tag_outs, total, page, page_size),
        )

    except Exception:
        handle_db_error("list tags")


def get_tag(db: Session, tag_id: int) -> TagOut:
    """Get a specific tag."""
    try:
        tag = db.query(Tag).filter(Tag.id == tag_id).first()

        if not tag:
            raise HTTPException(status_code=404, detail=f"Tag {tag_id} not found")

        return TagOut.model_validate(tag)

    except HTTPException:
        raise
    except Exception:
        handle_db_error(f"get tag {tag_id}")


def update_tag(db: Session, tag_id: int, tag_update: TagUpdate) -> TagOut:
    """Update a tag."""
    try:
        db_tag = db.query(Tag).filter(Tag.id == tag_id).first()
        if not db_tag:
            raise HTTPException(status_code=404, detail=f"Tag {tag_id} not found")

        # Update fields
        if tag_update.name is not None:
            db_tag.name = tag_update.name
        if tag_update.description is not None:
            db_tag.description = tag_update.description

        db.commit()
        db.refresh(db_tag)

        return TagOut.model_validate(db_tag)

    except HTTPException:
        raise
    except Exception:
        handle_db_error(f"update tag {tag_id}", db=db)


def delete_tag(db: Session, tag_id: int) -> None:
    """Delete a tag."""
    try:
        db_tag = db.query(Tag).filter(Tag.id == tag_id).first()
        if not db_tag:
            raise HTTPException(status_code=404, detail=f"Tag {tag_id} not found")

        db.delete(db_tag)
        db.commit()

    except HTTPException:
        raise
    except Exception:
        handle_db_error(f"delete tag {tag_id}", db=db)
