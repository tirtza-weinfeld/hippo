"""Example service - business logic for example operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException

from api.utils import handle_db_error
from db.models.dictionary import Definition, Example
from schemas.dictionary import ExampleBase, ExampleOut

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def create_example(
    db: Session,
    definition_id: int,
    example: ExampleBase,
) -> ExampleOut:
    """Add an example to an existing definition."""
    try:
        # Verify definition exists
        definition = db.query(Definition).filter(Definition.id == definition_id).first()
        if not definition:
            raise HTTPException(
                status_code=404,
                detail=f"Definition {definition_id} not found",
            )

        # Create example
        db_example = Example(
            definition_id=definition_id,
            example_text=example.example_text,
            source=example.source,
        )
        db.add(db_example)
        db.commit()
        db.refresh(db_example)

        return ExampleOut.model_validate(db_example)

    except HTTPException:
        raise
    except Exception:
        handle_db_error("create example", db=db)


def get_example(db: Session, example_id: int) -> ExampleOut:
    """Get a specific example."""
    try:
        example = db.query(Example).filter(Example.id == example_id).first()

        if not example:
            raise HTTPException(
                status_code=404,
                detail=f"Example {example_id} not found",
            )

        return ExampleOut.model_validate(example)

    except HTTPException:
        raise
    except Exception:
        handle_db_error(f"get example {example_id}")


def update_example(
    db: Session,
    example_id: int,
    example: ExampleBase,
) -> ExampleOut:
    """Update a specific example."""
    try:
        db_example = db.query(Example).filter(Example.id == example_id).first()
        if not db_example:
            raise HTTPException(
                status_code=404,
                detail=f"Example {example_id} not found",
            )

        # Update fields
        db_example.example_text = example.example_text
        db_example.source = example.source

        db.commit()
        db.refresh(db_example)

        return ExampleOut.model_validate(db_example)

    except HTTPException:
        raise
    except Exception:
        handle_db_error(f"update example {example_id}", db=db)


def delete_example(db: Session, example_id: int) -> None:
    """Delete a specific example."""
    try:
        db_example = db.query(Example).filter(Example.id == example_id).first()
        if not db_example:
            raise HTTPException(
                status_code=404,
                detail=f"Example {example_id} not found",
            )

        db.delete(db_example)
        db.commit()

    except HTTPException:
        raise
    except Exception:
        handle_db_error(f"delete example {example_id}", db=db)
