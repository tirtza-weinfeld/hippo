"""Vocabulary API routes for Oxford Languages-style dictionary database.

This module provides CRUD endpoints for managing vocabulary data:
- Words, Definitions, Examples
- Word Relations (synonyms, antonyms, etc.)
- Tags and categorization
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from db import get_db
from db.models.vocabulary import (
    Definition,
    Example,
    Tag,
    Word,
    WordRelation,
    WordTag,
)
from schemas.vocabulary import (
    DefinitionCreate,
    DefinitionOut,
    DefinitionUpdate,
    DefinitionWithExamples,
    ExampleCreate,
    ExampleOut,
    ExampleUpdate,
    TagCreate,
    TagOut,
    TagUpdate,
    TagWithWords,
    WordCreate,
    WordFull,
    WordOut,
    WordRelationCreate,
    WordRelationOut,
    WordTagOut,
    WordUpdate,
    WordWithTags,
)

router = APIRouter(prefix="/vocabulary", tags=["vocabulary"])


# ============================================================================
# Word Endpoints
# ============================================================================


@router.post("/words", response_model=WordOut, status_code=201)
def create_word(word: WordCreate, db: Session = Depends(get_db)) -> WordOut:
    """Create a new word entry.

    Args:
        word: Word data to create
        db: Database session

    Returns:
        Created word with ID and timestamp

    Raises:
        HTTPException: If word already exists for this language
    """
    try:
        # Check if word already exists for this language
        existing = (
            db.query(Word)
            .filter(
                Word.word_text == word.word_text,
                Word.language_code == word.language_code,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Word '{word.word_text}' already exists for language '{word.language_code}'",
            )

        db_word = Word(**word.model_dump())
        db.add(db_word)
        db.commit()
        db.refresh(db_word)
        return WordOut.model_validate(db_word)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to create word: {e}"
        ) from e


@router.get("/words/search", response_model=list[WordOut])
def search_words(
    q: str = Query(..., min_length=1, description="Search query for word text"),
    language: str | None = Query(None, description="Filter by language code"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum records to return (max 1000)"
    ),
    db: Session = Depends(get_db),
) -> list[WordOut]:
    """Search for words by text (case-insensitive partial match).

    Args:
        q: Search query string (required)
        language: Optional language code filter
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of matching words
    """
    try:
        query = db.query(Word).filter(Word.word_text.ilike(f"%{q}%"))
        if language:
            query = query.filter(Word.language_code == language)
        words = query.offset(skip).limit(limit).all()
        return [WordOut.model_validate(w) for w in words]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to search words: {e}"
        ) from e


@router.get("/words", response_model=list[WordOut])
def list_words(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum records to return (max 1000)"
    ),
    language: str | None = Query(None, description="Filter by language code"),
    db: Session = Depends(get_db),
) -> list[WordOut]:
    """List all words with optional language filter.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        language: Optional language code filter
        db: Database session

    Returns:
        List of words
    """
    try:
        query = db.query(Word)
        if language:
            query = query.filter(Word.language_code == language)
        words = query.offset(skip).limit(limit).all()
        return [WordOut.model_validate(w) for w in words]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list words: {e}") from e


@router.get("/words/{word_id}", response_model=WordFull)
def get_word(word_id: int, db: Session = Depends(get_db)) -> WordFull:
    """Get a word with all definitions and examples.

    Args:
        word_id: Word ID
        db: Database session

    Returns:
        Word with nested definitions and examples

    Raises:
        HTTPException: If word not found
    """
    try:
        word = (
            db.query(Word)
            .options(joinedload(Word.definitions).joinedload(Definition.examples))
            .filter(Word.id == word_id)
            .first()
        )
        if not word:
            raise HTTPException(status_code=404, detail=f"Word {word_id} not found")
        return WordFull.model_validate(word)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get word: {e}") from e


@router.patch("/words/{word_id}", response_model=WordOut)
def update_word(
    word_id: int, word_update: WordUpdate, db: Session = Depends(get_db)
) -> WordOut:
    """Update an existing word.

    Args:
        word_id: Word ID to update
        word_update: Updated word data
        db: Database session

    Returns:
        Updated word

    Raises:
        HTTPException: If word not found
    """
    try:
        db_word = db.query(Word).filter(Word.id == word_id).first()
        if not db_word:
            raise HTTPException(status_code=404, detail=f"Word {word_id} not found")

        update_data = word_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_word, key, value)

        db.commit()
        db.refresh(db_word)
        return WordOut.model_validate(db_word)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to update word: {e}"
        ) from e


@router.delete("/words/{word_id}", status_code=204, response_model=None)
def delete_word(word_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a word and all associated definitions/examples.

    Args:
        word_id: Word ID to delete
        db: Database session

    Raises:
        HTTPException: If word not found
    """
    try:
        db_word = db.query(Word).filter(Word.id == word_id).first()
        if not db_word:
            raise HTTPException(status_code=404, detail=f"Word {word_id} not found")

        db.delete(db_word)
        db.commit()
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to delete word: {e}"
        ) from e


# ============================================================================
# Definition Endpoints
# ============================================================================


@router.post("/definitions", response_model=DefinitionOut, status_code=201)
def create_definition(
    definition: DefinitionCreate, db: Session = Depends(get_db)
) -> DefinitionOut:
    """Create a new definition for a word.

    Args:
        definition: Definition data to create
        db: Database session

    Returns:
        Created definition

    Raises:
        HTTPException: If word doesn't exist or order conflicts
    """
    try:
        # Verify word exists
        word = db.query(Word).filter(Word.id == definition.word_id).first()
        if not word:
            raise HTTPException(
                status_code=404, detail=f"Word {definition.word_id} not found"
            )

        db_definition = Definition(**definition.model_dump())
        db.add(db_definition)
        db.commit()
        db.refresh(db_definition)
        return DefinitionOut.model_validate(db_definition)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to create definition: {e}"
        ) from e


@router.get("/definitions", response_model=list[DefinitionWithExamples])
def list_definitions(
    word_id: int | None = Query(None, description="Filter by word ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum records to return (max 1000)"
    ),
    db: Session = Depends(get_db),
) -> list[DefinitionWithExamples]:
    """List definitions with optional word filter.

    Args:
        word_id: Optional word ID to filter by
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of definitions with examples
    """
    try:
        query = db.query(Definition).options(joinedload(Definition.examples))
        if word_id:
            query = query.filter(Definition.word_id == word_id)
        definitions = query.offset(skip).limit(limit).all()
        return [DefinitionWithExamples.model_validate(d) for d in definitions]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list definitions: {e}"
        ) from e


@router.get("/definitions/{definition_id}", response_model=DefinitionWithExamples)
def get_definition(
    definition_id: int, db: Session = Depends(get_db)
) -> DefinitionWithExamples:
    """Get a specific definition with examples.

    Args:
        definition_id: Definition ID
        db: Database session

    Returns:
        Definition with examples

    Raises:
        HTTPException: If definition not found
    """
    try:
        definition = (
            db.query(Definition)
            .options(joinedload(Definition.examples))
            .filter(Definition.id == definition_id)
            .first()
        )
        if not definition:
            raise HTTPException(
                status_code=404, detail=f"Definition {definition_id} not found"
            )
        return DefinitionWithExamples.model_validate(definition)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get definition: {e}"
        ) from e


@router.patch("/definitions/{definition_id}", response_model=DefinitionOut)
def update_definition(
    definition_id: int,
    definition_update: DefinitionUpdate,
    db: Session = Depends(get_db),
) -> DefinitionOut:
    """Update an existing definition.

    Args:
        definition_id: Definition ID to update
        definition_update: Updated definition data
        db: Database session

    Returns:
        Updated definition

    Raises:
        HTTPException: If definition not found
    """
    try:
        db_definition = (
            db.query(Definition).filter(Definition.id == definition_id).first()
        )
        if not db_definition:
            raise HTTPException(
                status_code=404, detail=f"Definition {definition_id} not found"
            )

        update_data = definition_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_definition, key, value)

        db.commit()
        db.refresh(db_definition)
        return DefinitionOut.model_validate(db_definition)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to update definition: {e}"
        ) from e


@router.delete("/definitions/{definition_id}", status_code=204, response_model=None)
def delete_definition(definition_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a definition and associated examples.

    Args:
        definition_id: Definition ID to delete
        db: Database session

    Raises:
        HTTPException: If definition not found
    """
    try:
        db_definition = (
            db.query(Definition).filter(Definition.id == definition_id).first()
        )
        if not db_definition:
            raise HTTPException(
                status_code=404, detail=f"Definition {definition_id} not found"
            )

        db.delete(db_definition)
        db.commit()
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to delete definition: {e}"
        ) from e


# ============================================================================
# Example Endpoints
# ============================================================================


@router.post("/examples", response_model=ExampleOut, status_code=201)
def create_example(example: ExampleCreate, db: Session = Depends(get_db)) -> ExampleOut:
    """Create a new example for a definition.

    Args:
        example: Example data to create
        db: Database session

    Returns:
        Created example

    Raises:
        HTTPException: If definition doesn't exist
    """
    try:
        # Verify definition exists
        definition = (
            db.query(Definition).filter(Definition.id == example.definition_id).first()
        )
        if not definition:
            raise HTTPException(
                status_code=404, detail=f"Definition {example.definition_id} not found"
            )

        db_example = Example(**example.model_dump())
        db.add(db_example)
        db.commit()
        db.refresh(db_example)
        return ExampleOut.model_validate(db_example)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to create example: {e}"
        ) from e


@router.get("/examples", response_model=list[ExampleOut])
def list_examples(
    definition_id: int | None = Query(None, description="Filter by definition ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum records to return (max 1000)"
    ),
    db: Session = Depends(get_db),
) -> list[ExampleOut]:
    """List examples with optional definition filter.

    Args:
        definition_id: Optional definition ID to filter by
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of examples
    """
    try:
        query = db.query(Example)
        if definition_id:
            query = query.filter(Example.definition_id == definition_id)
        examples = query.offset(skip).limit(limit).all()
        return [ExampleOut.model_validate(e) for e in examples]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list examples: {e}"
        ) from e


@router.patch("/examples/{example_id}", response_model=ExampleOut)
def update_example(
    example_id: int,
    example_update: ExampleUpdate,
    db: Session = Depends(get_db),
) -> ExampleOut:
    """Update an existing example.

    Args:
        example_id: Example ID to update
        example_update: Updated example data
        db: Database session

    Returns:
        Updated example

    Raises:
        HTTPException: If example not found
    """
    try:
        db_example = db.query(Example).filter(Example.id == example_id).first()
        if not db_example:
            raise HTTPException(
                status_code=404, detail=f"Example {example_id} not found"
            )

        update_data = example_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_example, key, value)

        db.commit()
        db.refresh(db_example)
        return ExampleOut.model_validate(db_example)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to update example: {e}"
        ) from e


@router.delete("/examples/{example_id}", status_code=204, response_model=None)
def delete_example(example_id: int, db: Session = Depends(get_db)) -> None:
    """Delete an example.

    Args:
        example_id: Example ID to delete
        db: Database session

    Raises:
        HTTPException: If example not found
    """
    try:
        db_example = db.query(Example).filter(Example.id == example_id).first()
        if not db_example:
            raise HTTPException(
                status_code=404, detail=f"Example {example_id} not found"
            )

        db.delete(db_example)
        db.commit()
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to delete example: {e}"
        ) from e


# ============================================================================
# Word Relation Endpoints
# ============================================================================


@router.post("/word-relations", response_model=WordRelationOut, status_code=201)
def create_word_relation(
    relation: WordRelationCreate, db: Session = Depends(get_db)
) -> WordRelationOut:
    """Create a relation between two words (synonym, antonym, etc.).

    Args:
        relation: Word relation data
        db: Database session

    Returns:
        Created word relation

    Raises:
        HTTPException: If words don't exist or relation already exists
    """
    try:
        # Verify both words exist
        word1 = db.query(Word).filter(Word.id == relation.word_id_1).first()
        word2 = db.query(Word).filter(Word.id == relation.word_id_2).first()
        if not word1:
            raise HTTPException(
                status_code=404, detail=f"Word {relation.word_id_1} not found"
            )
        if not word2:
            raise HTTPException(
                status_code=404, detail=f"Word {relation.word_id_2} not found"
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
            raise HTTPException(status_code=400, detail="Word relation already exists")

        db_relation = WordRelation(**relation.model_dump())
        db.add(db_relation)
        db.commit()
        db.refresh(db_relation)
        return WordRelationOut.model_validate(db_relation)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to create word relation: {e}"
        ) from e


@router.get("/word-relations", response_model=list[WordRelationOut])
def list_word_relations(
    word_id: int | None = Query(
        None, description="Filter by word ID (either side of relation)"
    ),
    relation_type: str | None = Query(None, description="Filter by relation type"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum records to return (max 1000)"
    ),
    db: Session = Depends(get_db),
) -> list[WordRelationOut]:
    """List word relations with optional filters.

    Args:
        word_id: Optional word ID to filter by (either side of relation)
        relation_type: Optional relation type filter
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of word relations
    """
    try:
        query = db.query(WordRelation)
        if word_id:
            query = query.filter(
                (WordRelation.word_id_1 == word_id)
                | (WordRelation.word_id_2 == word_id)
            )
        if relation_type:
            query = query.filter(WordRelation.relation_type == relation_type)
        relations = query.offset(skip).limit(limit).all()
        return [WordRelationOut.model_validate(r) for r in relations]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list word relations: {e}"
        ) from e


@router.delete(
    "/word-relations/{word_id_1}/{word_id_2}", status_code=204, response_model=None
)
def delete_word_relation(
    word_id_1: int,
    word_id_2: int,
    relation_type: str,
    db: Session = Depends(get_db),
) -> None:
    """Delete a word relation.

    Args:
        word_id_1: First word ID
        word_id_2: Second word ID
        relation_type: Type of relation
        db: Database session

    Raises:
        HTTPException: If relation not found
    """
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
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to delete word relation: {e}"
        ) from e


# ============================================================================
# Tag Endpoints
# ============================================================================


@router.post("/tags", response_model=TagOut, status_code=201)
def create_tag(tag: TagCreate, db: Session = Depends(get_db)) -> TagOut:
    """Create a new tag for categorizing words.

    Args:
        tag: Tag data to create
        db: Database session

    Returns:
        Created tag

    Raises:
        HTTPException: If tag name already exists
    """
    try:
        # Check if tag already exists
        existing = db.query(Tag).filter(Tag.name == tag.name).first()
        if existing:
            raise HTTPException(
                status_code=400, detail=f"Tag '{tag.name}' already exists"
            )

        db_tag = Tag(**tag.model_dump())
        db.add(db_tag)
        db.commit()
        db.refresh(db_tag)
        return TagOut.model_validate(db_tag)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create tag: {e}") from e


@router.get("/tags", response_model=list[TagOut])
def list_tags(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum records to return (max 1000)"
    ),
    db: Session = Depends(get_db),
) -> list[TagOut]:
    """List all tags.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of tags
    """
    try:
        tags = db.query(Tag).offset(skip).limit(limit).all()
        return [TagOut.model_validate(t) for t in tags]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tags: {e}") from e


@router.get("/tags/{tag_id}", response_model=TagWithWords)
def get_tag(tag_id: int, db: Session = Depends(get_db)) -> TagWithWords:
    """Get a tag with all associated words.

    Args:
        tag_id: Tag ID
        db: Database session

    Returns:
        Tag with associated words

    Raises:
        HTTPException: If tag not found
    """
    try:
        tag = (
            db.query(Tag)
            .options(joinedload(Tag.words))
            .filter(Tag.id == tag_id)
            .first()
        )
        if not tag:
            raise HTTPException(status_code=404, detail=f"Tag {tag_id} not found")
        return TagWithWords.model_validate(tag)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tag: {e}") from e


@router.patch("/tags/{tag_id}", response_model=TagOut)
def update_tag(
    tag_id: int, tag_update: TagUpdate, db: Session = Depends(get_db)
) -> TagOut:
    """Update an existing tag.

    Args:
        tag_id: Tag ID to update
        tag_update: Updated tag data
        db: Database session

    Returns:
        Updated tag

    Raises:
        HTTPException: If tag not found
    """
    try:
        db_tag = db.query(Tag).filter(Tag.id == tag_id).first()
        if not db_tag:
            raise HTTPException(status_code=404, detail=f"Tag {tag_id} not found")

        update_data = tag_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_tag, key, value)

        db.commit()
        db.refresh(db_tag)
        return TagOut.model_validate(db_tag)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update tag: {e}") from e


@router.delete("/tags/{tag_id}", status_code=204, response_model=None)
def delete_tag(tag_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a tag.

    Args:
        tag_id: Tag ID to delete
        db: Database session

    Raises:
        HTTPException: If tag not found
    """
    try:
        db_tag = db.query(Tag).filter(Tag.id == tag_id).first()
        if not db_tag:
            raise HTTPException(status_code=404, detail=f"Tag {tag_id} not found")

        db.delete(db_tag)
        db.commit()
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete tag: {e}") from e


# ============================================================================
# Word-Tag Association Endpoints
# ============================================================================


@router.post(
    "/words/{word_id}/tags/{tag_id}", response_model=WordTagOut, status_code=201
)
def add_tag_to_word(
    word_id: int, tag_id: int, db: Session = Depends(get_db)
) -> WordTagOut:
    """Associate a tag with a word.

    Args:
        word_id: Word ID
        tag_id: Tag ID
        db: Database session

    Returns:
        Created word-tag association

    Raises:
        HTTPException: If word/tag doesn't exist or association already exists
    """
    try:
        # Verify word and tag exist
        word = db.query(Word).filter(Word.id == word_id).first()
        tag = db.query(Tag).filter(Tag.id == tag_id).first()
        if not word:
            raise HTTPException(status_code=404, detail=f"Word {word_id} not found")
        if not tag:
            raise HTTPException(status_code=404, detail=f"Tag {tag_id} not found")

        # Check if association already exists
        existing = (
            db.query(WordTag)
            .filter(WordTag.word_id == word_id, WordTag.tag_id == tag_id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=400, detail="Word-tag association already exists"
            )

        db_word_tag = WordTag(word_id=word_id, tag_id=tag_id)
        db.add(db_word_tag)
        db.commit()
        db.refresh(db_word_tag)
        return WordTagOut.model_validate(db_word_tag)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to add tag to word: {e}"
        ) from e


@router.delete("/words/{word_id}/tags/{tag_id}", status_code=204, response_model=None)
def remove_tag_from_word(
    word_id: int, tag_id: int, db: Session = Depends(get_db)
) -> None:
    """Remove a tag from a word.

    Args:
        word_id: Word ID
        tag_id: Tag ID
        db: Database session

    Raises:
        HTTPException: If association not found
    """
    try:
        db_word_tag = (
            db.query(WordTag)
            .filter(WordTag.word_id == word_id, WordTag.tag_id == tag_id)
            .first()
        )
        if not db_word_tag:
            raise HTTPException(
                status_code=404, detail="Word-tag association not found"
            )

        db.delete(db_word_tag)
        db.commit()
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to remove tag from word: {e}"
        ) from e


@router.get("/words/{word_id}/tags", response_model=WordWithTags)
def get_word_with_tags(word_id: int, db: Session = Depends(get_db)) -> WordWithTags:
    """Get a word with all its tags.

    Args:
        word_id: Word ID
        db: Database session

    Returns:
        Word with associated tags

    Raises:
        HTTPException: If word not found
    """
    try:
        word = (
            db.query(Word)
            .options(joinedload(Word.tags))
            .filter(Word.id == word_id)
            .first()
        )
        if not word:
            raise HTTPException(status_code=404, detail=f"Word {word_id} not found")
        return WordWithTags.model_validate(word)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get word with tags: {e}"
        ) from e
