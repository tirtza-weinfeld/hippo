"""Definition service - business logic for definition operations."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from api.utils import handle_db_error
from db.models.dictionary import Definition, Example, Word
from schemas.dictionary import DefinitionNested, DefinitionOut


def create_definition(
    db: Session,
    word_id: int,
    definition: DefinitionNested,
) -> DefinitionOut:
    """Add a definition to an existing word."""
    try:
        # Verify word exists
        word = db.query(Word).filter(Word.id == word_id).first()
        if not word:
            raise HTTPException(status_code=404, detail=f"Word {word_id} not found")

        # Create definition
        db_definition = Definition(
            word_id=word_id,
            definition_text=definition.definition_text,
            part_of_speech=definition.part_of_speech,
            order=definition.order,
        )
        db.add(db_definition)
        db.flush()

        # Create examples
        for example_data in definition.examples:
            db_example = Example(
                definition_id=db_definition.id,
                example_text=example_data.example_text,
                source=example_data.source,
            )
            db.add(db_example)

        db.commit()
        db.refresh(db_definition)

        # Load with examples
        definition_with_examples = (
            db.query(Definition)
            .options(joinedload(Definition.examples))
            .filter(Definition.id == db_definition.id)
            .first()
        )

        return DefinitionOut.model_validate(definition_with_examples)

    except HTTPException:
        raise
    except Exception:
        handle_db_error("create definition", db=db)


def get_definition(db: Session, definition_id: int) -> DefinitionOut:
    """Get a specific definition with examples."""
    try:
        definition = (
            db.query(Definition)
            .options(joinedload(Definition.examples))
            .filter(Definition.id == definition_id)
            .first()
        )

        if not definition:
            raise HTTPException(
                status_code=404,
                detail=f"Definition {definition_id} not found",
            )

        return DefinitionOut.model_validate(definition)

    except HTTPException:
        raise
    except Exception:
        handle_db_error(f"get definition {definition_id}")


def update_definition(
    db: Session,
    definition_id: int,
    definition: DefinitionNested,
) -> DefinitionOut:
    """Update a specific definition."""
    try:
        db_definition = (
            db.query(Definition).filter(Definition.id == definition_id).first()
        )
        if not db_definition:
            raise HTTPException(
                status_code=404,
                detail=f"Definition {definition_id} not found",
            )

        # Update definition fields
        db_definition.definition_text = definition.definition_text
        db_definition.part_of_speech = definition.part_of_speech
        db_definition.order = definition.order

        # Replace examples
        _ = db.query(Example).filter(Example.definition_id == definition_id).delete()
        for example_data in definition.examples:
            db_example = Example(
                definition_id=definition_id,
                example_text=example_data.example_text,
                source=example_data.source,
            )
            db.add(db_example)

        db.commit()

        # Load with examples
        definition_with_examples = (
            db.query(Definition)
            .options(joinedload(Definition.examples))
            .filter(Definition.id == definition_id)
            .first()
        )

        return DefinitionOut.model_validate(definition_with_examples)

    except HTTPException:
        raise
    except Exception:
        handle_db_error(f"update definition {definition_id}", db=db)


def delete_definition(db: Session, definition_id: int) -> None:
    """Delete a definition (cascades to examples)."""
    try:
        db_definition = (
            db.query(Definition).filter(Definition.id == definition_id).first()
        )
        if not db_definition:
            raise HTTPException(
                status_code=404,
                detail=f"Definition {definition_id} not found",
            )

        db.delete(db_definition)
        db.commit()

    except HTTPException:
        raise
    except Exception:
        handle_db_error(f"delete definition {definition_id}", db=db)
