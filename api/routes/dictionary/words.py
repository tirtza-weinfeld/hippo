"""Word endpoints for dictionary API.

Thin route handlers - business logic in services.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.services import word_service
from db import get_db
from schemas.dictionary import (
    PaginatedResponse,
    PaginatedWords,
    WordCreate,
    WordFull,
    WordOut,
    WordUpdate,
)

router = APIRouter(prefix="/words", tags=["words"])


@router.post(
    "",
    response_model=WordOut | WordFull | list[WordOut] | list[WordFull],
    status_code=201,
)
def create_words(
    word_data: WordCreate | list[WordCreate],
    db: Annotated[Session, Depends(get_db)],
) -> WordOut | WordFull | list[WordOut] | list[WordFull]:
    """Create one or more words with optional nested data.

    Examples:
        Simple: {"word_text": "hello", "language_code": "en"}
        Nested: {..., "definitions": [...], "tag_ids": [1, 2]}
        Multiple: [{"word_text": "word1", ...}, {"word_text": "word2", ...}]
    """
    return word_service.create_words(db, word_data)


@router.get("", response_model=PaginatedWords | PaginatedResponse[WordFull])
def list_words(
    db: Annotated[Session, Depends(get_db)],
    search: Annotated[str | None, Query(description="Search word text")] = None,
    language: Annotated[
        str | None, Query(description="Filter by language code")
    ] = None,
    include_all: Annotated[bool, Query(description="Include all nested data")] = False,
    include_definitions: Annotated[
        bool, Query(description="Include definitions")
    ] = False,
    include_tags: Annotated[bool, Query(description="Include tags")] = False,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> PaginatedWords | PaginatedResponse[WordFull]:
    """List or search words (returns basic fields by default)."""
    return word_service.list_words(
        db,
        search,
        language,
        page,
        page_size,
        include_all,
        include_definitions,
        include_tags,
    )


@router.get("/{language_code}/{word_text}", response_model=WordOut | WordFull)
def get_word_by_text(
    language_code: str,
    word_text: str,
    db: Annotated[Session, Depends(get_db)],
    include_all: Annotated[bool, Query(description="Include all nested data")] = True,
    include_definitions: Annotated[
        bool, Query(description="Include definitions")
    ] = False,
    include_tags: Annotated[bool, Query(description="Include tags")] = False,
) -> WordOut | WordFull:
    """Get a specific word by text and language (returns full data by default)."""
    return word_service.get_word_by_text(
        db,
        word_text,
        language_code,
        include_all,
        include_definitions,
        include_tags,
    )


@router.get("/{word_id}", response_model=WordOut | WordFull)
def get_word(
    word_id: int,
    db: Annotated[Session, Depends(get_db)],
    include_all: Annotated[bool, Query(description="Include all nested data")] = False,
    include_definitions: Annotated[
        bool, Query(description="Include definitions")
    ] = False,
    include_tags: Annotated[bool, Query(description="Include tags")] = False,
) -> WordOut | WordFull:
    """Get a specific word (returns basic fields by default)."""
    return word_service.get_word(
        db,
        word_id,
        include_all,
        include_definitions,
        include_tags,
    )


@router.patch("/{word_id}", response_model=WordOut | WordFull)
def update_word(
    word_id: int,
    word_update: WordUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> WordOut | WordFull:
    """Update a word with optional nested data.

    Examples:
        Simple: {"word_text": "updated"}
        With definitions: {"definitions": [{"id": 1, "definition_text": "..."}]}
        With tags: {"tag_ids": [1, 2, 3]}
    """
    return word_service.update_word(db, word_id, word_update)


@router.delete("/{word_id}", status_code=204, response_model=None)
def delete_word(
    word_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Delete a word (cascades to definitions, examples)."""
    word_service.delete_word(db, word_id)
