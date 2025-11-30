"""Word service - business logic for word operations.

Handles word CRUD including nested data (definitions, examples, tags).
"""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import tuple_
from sqlalchemy.orm import Session, joinedload

from api.services.tag_service import get_or_create_tags
from api.utils import build_paginated_response, handle_db_error
from db.models.dictionary import Definition, Example, Word, WordForm, WordTag
from schemas.dictionary import (
    PaginatedResponse,
    PaginatedWords,
    WordCreate,
    WordFull,
    WordOut,
    WordUpdate,
)


def create_words(
    db: Session,
    word_data: WordCreate | list[WordCreate],
) -> WordOut | WordFull | list[WordOut] | list[WordFull]:
    """Create one or more words with optional nested data.

    Args:
        db: Database session
        word_data: Single word or list of words

    Returns:
        Created word(s) - WordOut for simple, WordFull for nested
    """
    if isinstance(word_data, list):
        return _create_words_bulk(db, word_data)
    return _create_single_word(db, word_data)


def _create_single_word(db: Session, word_data: WordCreate) -> WordOut | WordFull:
    """Create a single word with optional nested data."""
    try:
        # Check if word already exists
        existing = (
            db.query(Word)
            .filter(
                Word.word_text == word_data.word_text,
                Word.language_code == word_data.language_code,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Word '{word_data.word_text}' already exists "
                    f"for language '{word_data.language_code}'"
                ),
            )

        # Check if nested creation
        has_nested_data = (
            word_data.definitions or word_data.tags or word_data.word_forms
        )

        if has_nested_data:
            return _create_word_with_nested_data(db, word_data)

        # Simple word creation
        db_word = Word(
            word_text=word_data.word_text,
            language_code=word_data.language_code,
        )
        db.add(db_word)
        db.commit()
        db.refresh(db_word)
        return WordOut.model_validate(db_word)

    except HTTPException:
        raise
    except Exception:
        handle_db_error("create word", db=db)


def _create_word_with_nested_data(db: Session, word_data: WordCreate) -> WordFull:
    """Create a word with all nested data (definitions, examples, tags)."""
    try:
        # Get or create tags by name
        tag_ids = get_or_create_tags(db, word_data.tags)

        # Create word
        db_word = Word(
            word_text=word_data.word_text,
            language_code=word_data.language_code,
        )
        db.add(db_word)
        db.flush()

        # Create definitions and examples
        for def_data in word_data.definitions:
            db_definition = Definition(
                word_id=db_word.id,
                definition_text=def_data.definition_text,
                part_of_speech=def_data.part_of_speech,
                order=def_data.order,
            )
            db.add(db_definition)
            db.flush()

            # Create examples
            for example_data in def_data.examples:
                db_example = Example(
                    definition_id=db_definition.id,
                    example_text=example_data.example_text,
                    source=example_data.source,
                )
                db.add(db_example)

        # Associate tags
        for tag_id in tag_ids:
            db_word_tag = WordTag(word_id=db_word.id, tag_id=tag_id)
            db.add(db_word_tag)

        # Create word forms (inflections)
        for form_data in word_data.word_forms:
            db_word_form = WordForm(
                word_id=db_word.id,
                form_text=form_data.form_text,
                form_type=form_data.form_type,
            )
            db.add(db_word_form)

        db.commit()

        # Fetch complete word with nested data
        word = (
            db.query(Word)
            .options(
                joinedload(Word.definitions).joinedload(Definition.examples),
                joinedload(Word.tags),
                joinedload(Word.word_forms),
            )
            .filter(Word.id == db_word.id)
            .first()
        )
        return WordFull.model_validate(word)

    except HTTPException:
        raise
    except Exception:
        handle_db_error("create word with nested data", db=db)


def _create_words_bulk(
    db: Session, words: list[WordCreate]
) -> list[WordOut] | list[WordFull]:
    """Create multiple words in a single transaction."""
    try:
        if not words:
            raise HTTPException(status_code=400, detail="No words provided")

        # Check for duplicates in request
        word_keys = [(w.word_text, w.language_code) for w in words]
        if len(word_keys) != len(set(word_keys)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate words found in request",
            )

        # Check if any words already exist
        existing_words = (
            db.query(Word.word_text, Word.language_code)
            .filter(tuple_(Word.word_text, Word.language_code).in_(word_keys))
            .all()
        )
        if existing_words:
            duplicates = [f"{text} ({lang})" for text, lang in existing_words]
            raise HTTPException(
                status_code=400,
                detail=f"Words already exist: {', '.join(duplicates)}",
            )

        # Check if any have nested data
        has_nested = any(w.definitions or w.tags or w.word_forms for w in words)

        if has_nested:
            # Create one by one to handle nested data
            return [_create_word_with_nested_data(db, w) for w in words]

        # Simple bulk creation
        db_words = [
            Word(word_text=w.word_text, language_code=w.language_code) for w in words
        ]
        db.add_all(db_words)
        db.commit()

        for db_word in db_words:
            db.refresh(db_word)

        return [WordOut.model_validate(w) for w in db_words]

    except HTTPException:
        raise
    except Exception:
        handle_db_error("create words in bulk", db=db)


def list_words(
    db: Session,
    search: str | None,
    language: str | None,
    page: int,
    page_size: int,
    include_all: bool,
    include_definitions: bool,
    include_tags: bool,
) -> PaginatedWords | PaginatedResponse[WordFull]:
    """List or search words with pagination (returns basic fields by default).

    Search includes word forms (inflections) - searching "defying" finds "defy".
    """
    try:
        query = db.query(Word)

        # Apply filters
        if search:
            # Search by word text OR word forms (Oxford approach)
            # Searching "defying" should find the word "defy"
            from sqlalchemy import or_

            query = query.outerjoin(WordForm).filter(
                or_(
                    Word.word_text.ilike(f"{search}%"),
                    WordForm.form_text.ilike(f"{search}%"),
                )
            )
        if language:
            query = query.filter(Word.language_code == language)

        # Load nested data if requested
        if include_all or include_definitions:
            query = query.options(
                joinedload(Word.definitions).joinedload(Definition.examples),
            )
        if include_all or include_tags:
            query = query.options(joinedload(Word.tags))

        # Always load word_forms to avoid N+1 queries
        query = query.options(joinedload(Word.word_forms))

        # Order by word text and remove duplicates from outer join
        query = query.distinct().order_by(Word.word_text.asc())

        # Paginate
        total = query.count()
        skip = (page - 1) * page_size
        words = query.offset(skip).limit(page_size).all()

        # Return WordFull if any nested data requested, otherwise WordOut
        if include_all or include_definitions or include_tags:
            word_fulls = [WordFull.model_validate(w) for w in words]
            return PaginatedResponse[WordFull].model_validate(
                build_paginated_response(word_fulls, total, page, page_size),
            )

        word_outs = [WordOut.model_validate(w) for w in words]
        return PaginatedWords.model_validate(
            build_paginated_response(word_outs, total, page, page_size),
        )

    except Exception:
        handle_db_error("list words")


def get_word(
    db: Session,
    word_id: int,
    include_all: bool,
    include_definitions: bool,
    include_tags: bool,
) -> WordOut | WordFull:
    """Get a specific word (returns basic fields by default)."""
    try:
        query = db.query(Word)

        # Load requested nested data
        if include_all or include_definitions:
            query = query.options(
                joinedload(Word.definitions).joinedload(Definition.examples),
            )

        if include_all or include_tags:
            query = query.options(joinedload(Word.tags))

        word = query.filter(Word.id == word_id).first()

        if not word:
            raise HTTPException(status_code=404, detail=f"Word {word_id} not found")

        # Return WordFull if any nested data requested, otherwise WordOut
        if include_all or include_definitions or include_tags:
            return WordFull.model_validate(word)

        return WordOut.model_validate(word)

    except HTTPException:
        raise
    except Exception:
        handle_db_error(f"get word {word_id}")


def get_word_by_text(
    db: Session,
    word_text: str,
    language_code: str,
    include_all: bool,
    include_definitions: bool,
    include_tags: bool,
) -> WordOut | WordFull:
    """Get a specific word by text and language (returns basic fields by default)."""
    try:
        query = db.query(Word)

        # Load requested nested data
        if include_all or include_definitions:
            query = query.options(
                joinedload(Word.definitions).joinedload(Definition.examples),
            )

        if include_all or include_tags:
            query = query.options(joinedload(Word.tags))

        word = query.filter(
            Word.word_text == word_text,
            Word.language_code == language_code,
        ).first()

        if not word:
            raise HTTPException(
                status_code=404,
                detail=f"Word '{word_text}' not found for language '{language_code}'",
            )

        # Return WordFull if any nested data requested, otherwise WordOut
        if include_all or include_definitions or include_tags:
            return WordFull.model_validate(word)

        return WordOut.model_validate(word)

    except HTTPException:
        raise
    except Exception:
        handle_db_error(f"get word '{word_text}' for language '{language_code}'")


def update_word(
    db: Session,
    word_id: int,
    word_update: WordUpdate,
) -> WordOut | WordFull:
    """Update a word with optional nested data.

    Note: updated_at is automatically updated by event listeners when
    word fields or nested data (definitions, examples, tags) change.
    """
    try:
        db_word = db.query(Word).filter(Word.id == word_id).first()
        if not db_word:
            raise HTTPException(status_code=404, detail=f"Word {word_id} not found")

        # Update word fields
        if word_update.word_text is not None:
            db_word.word_text = word_update.word_text
        if word_update.language_code is not None:
            db_word.language_code = word_update.language_code

        # Check if nested update
        has_nested = word_update.definitions is not None or word_update.tags is not None

        if has_nested:
            return _update_word_with_nested_data(db, word_id, word_update)

        # Simple update
        db.commit()
        db.refresh(db_word)
        return WordOut.model_validate(db_word)

    except HTTPException:
        raise
    except Exception:
        handle_db_error(f"update word {word_id}", db=db)


def _update_word_with_nested_data(
    db: Session,
    word_id: int,
    word_update: WordUpdate,
) -> WordFull:
    """Update word with nested data (definitions, examples, tags)."""
    try:
        # Update definitions
        if word_update.definitions is not None:
            for def_data in word_update.definitions:
                if def_data.id:
                    # Update existing definition
                    db_def = (
                        db.query(Definition)
                        .filter(
                            Definition.id == def_data.id,
                            Definition.word_id == word_id,
                        )
                        .first()
                    )
                    if not db_def:
                        raise HTTPException(
                            status_code=404,
                            detail=f"Definition {def_data.id} not found for word {word_id}",
                        )

                    db_def.definition_text = def_data.definition_text
                    db_def.part_of_speech = def_data.part_of_speech
                    db_def.order = def_data.order

                    # Replace examples
                    _ = (
                        db.query(Example)
                        .filter(Example.definition_id == db_def.id)
                        .delete()
                    )
                    for example_data in def_data.examples:
                        db_example = Example(
                            definition_id=db_def.id,
                            example_text=example_data.example_text,
                            source=example_data.source,
                        )
                        db.add(db_example)
                else:
                    # Create new definition
                    db_def = Definition(
                        word_id=word_id,
                        definition_text=def_data.definition_text,
                        part_of_speech=def_data.part_of_speech,
                        order=def_data.order,
                    )
                    db.add(db_def)
                    db.flush()

                    for example_data in def_data.examples:
                        db_example = Example(
                            definition_id=db_def.id,
                            example_text=example_data.example_text,
                            source=example_data.source,
                        )
                        db.add(db_example)

        # Update tags
        if word_update.tags is not None:
            # Get or create tags by name
            tag_ids = get_or_create_tags(db, word_update.tags)

            # Replace all tags
            _ = db.query(WordTag).filter(WordTag.word_id == word_id).delete()
            for tag_id in tag_ids:
                db_word_tag = WordTag(word_id=word_id, tag_id=tag_id)
                db.add(db_word_tag)

        db.commit()

        # Fetch complete word
        word = (
            db.query(Word)
            .options(
                joinedload(Word.definitions).joinedload(Definition.examples),
                joinedload(Word.tags),
            )
            .filter(Word.id == word_id)
            .first()
        )
        return WordFull.model_validate(word)

    except HTTPException:
        raise
    except Exception:
        handle_db_error(f"update word {word_id} with nested data", db=db)


def delete_word(db: Session, word_id: int) -> None:
    """Delete a word (cascades to definitions, examples)."""
    try:
        db_word = db.query(Word).filter(Word.id == word_id).first()
        if not db_word:
            raise HTTPException(status_code=404, detail=f"Word {word_id} not found")

        db.delete(db_word)
        db.commit()

    except HTTPException:
        raise
    except Exception:
        handle_db_error(f"delete word {word_id}", db=db)
