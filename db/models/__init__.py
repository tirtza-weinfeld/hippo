"""SQLAlchemy models for dictionary database."""

from __future__ import annotations

from db.models.dictionary import (
    Definition,
    Example,
    Tag,
    Word,
    WordRelation,
    WordTag,
)

__all__ = ["Definition", "Example", "Tag", "Word", "WordRelation", "WordTag"]
