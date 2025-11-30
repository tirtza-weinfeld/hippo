"""Relation service - business logic for word relation operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException

from api.utils import build_paginated_response, handle_db_error
from db.models.dictionary import Word, WordRelation
from schemas.dictionary import PaginatedRelations, RelationCreate, RelationOut

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def create_relation(db: Session, relation: RelationCreate) -> RelationOut:
    """Create a word relation (synonym, antonym, etc)."""
    try:
        # Verify both words exist
        word1 = db.query(Word).filter(Word.id == relation.word_id_1).first()
        word2 = db.query(Word).filter(Word.id == relation.word_id_2).first()

        if not word1:
            raise HTTPException(
                status_code=404,
                detail=f"Word {relation.word_id_1} not found",
            )
        if not word2:
            raise HTTPException(
                status_code=404,
                detail=f"Word {relation.word_id_2} not found",
            )

        # Check if relation already exists
        existing = (
            db.query(WordRelation)
            .filter(
                WordRelation.word_id_1 == relation.word_id_1,
                WordRelation.word_id_2 == relation.word_id_2,
                WordRelation.relation_type == relation.relation_type,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Word relation already exists",
            )

        db_relation = WordRelation(
            word_id_1=relation.word_id_1,
            word_id_2=relation.word_id_2,
            relation_type=relation.relation_type,
        )
        db.add(db_relation)
        db.commit()
        db.refresh(db_relation)

        return RelationOut.model_validate(db_relation)

    except HTTPException:
        raise
    except Exception:
        handle_db_error("create relation", db=db)


def list_relations(
    db: Session,
    word_id: int | None,
    relation_type: str | None,
    page: int,
    page_size: int,
) -> PaginatedRelations:
    """List word relations with optional filters."""
    try:
        query = db.query(WordRelation)

        # Apply filters
        if word_id:
            query = query.filter(
                (WordRelation.word_id_1 == word_id)
                | (WordRelation.word_id_2 == word_id),
            )
        if relation_type:
            query = query.filter(WordRelation.relation_type == relation_type)

        # Paginate
        total = query.count()
        skip = (page - 1) * page_size
        relations = query.offset(skip).limit(page_size).all()

        relation_outs = [RelationOut.model_validate(r) for r in relations]
        return PaginatedRelations.model_validate(
            build_paginated_response(relation_outs, total, page, page_size),
        )

    except Exception:
        handle_db_error("list relations")


def delete_relation(
    db: Session,
    word_id_1: int,
    word_id_2: int,
    relation_type: str,
) -> None:
    """Delete a word relation."""
    try:
        db_relation = (
            db.query(WordRelation)
            .filter(
                WordRelation.word_id_1 == word_id_1,
                WordRelation.word_id_2 == word_id_2,
                WordRelation.relation_type == relation_type,
            )
            .first()
        )

        if not db_relation:
            raise HTTPException(status_code=404, detail="Word relation not found")

        db.delete(db_relation)
        db.commit()

    except HTTPException:
        raise
    except Exception:
        handle_db_error("delete relation", db=db)
