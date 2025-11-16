"""SQLAlchemy models for vocabulary database."""

from __future__ import annotations

from db.models.vocabulary import (
    Definition,
    Example,
    Tag,
    Word,
    WordRelation,
    WordTag,
)

__all__ = ["Word", "Definition", "Example", "WordRelation", "Tag", "WordTag"]
