"""SQLAlchemy models for dictionary database (Oxford Languages-style).

This module defines a normalized relational schema for storing dictionary data:
- Words can have multiple definitions
- Definitions can have multiple examples
- Words can be related to other words (synonyms, antonyms)
- Words can be organized with tags/categories (many-to-many)
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    event,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class PartOfSpeech(str, Enum):
    """Part of speech for definitions."""

    NOUN = "noun"
    VERB = "verb"
    ADJECTIVE = "adjective"
    ADVERB = "adverb"
    PRONOUN = "pronoun"
    PREPOSITION = "preposition"
    CONJUNCTION = "conjunction"
    INTERJECTION = "interjection"
    DETERMINER = "determiner"
    AUXILIARY = "auxiliary"
    PHRASE = "phrase"
    OTHER = "other"


class RelationType(str, Enum):
    """Type of relationship between words."""

    SYNONYM = "synonym"
    ANTONYM = "antonym"
    HYPERNYM = "hypernym"  # more general term (animal -> dog)
    HYPONYM = "hyponym"  # more specific term (dog -> animal)
    MERONYM = "meronym"  # part of (wheel -> car)
    HOLONYM = "holonym"  # whole of (car -> wheel)
    RELATED = "related"  # general semantic relation


class Word(Base):
    """Core dictionary entry.

    A word can exist without definitions (allows gradual data entry).
    Multiple definitions can be associated with one word.
    """

    __tablename__ = "words"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    word_text: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    language_code: Mapped[str] = mapped_column(
        String(10), nullable=False, index=True
    )  # e.g., "en", "es", "fr"
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    definitions: Mapped[list[Definition]] = relationship(
        "Definition",
        back_populates="word",
        cascade="all, delete-orphan",
    )
    tags: Mapped[list[Tag]] = relationship(
        "Tag",
        secondary="word_tags",
        back_populates="words",
    )
    word_forms: Mapped[list[WordForm]] = relationship(
        "WordForm",
        back_populates="word",
        cascade="all, delete-orphan",
    )

    # Self-referential relationships for word relations
    # This is handled via the WordRelation table

    __table_args__ = (
        # Ensure unique (word_text, language_code) pairs
        UniqueConstraint("word_text", "language_code", name="uq_word_language"),
        # Index for searching by word prefix
        Index("idx_word_text_lower", "word_text"),
    )

    def __repr__(self) -> str:
        return f"<Word(id={self.id}, word='{self.word_text}', lang='{self.language_code}')>"


class Definition(Base):
    """Multiple definitions per word.

    Each definition has a specific part of speech and can have multiple examples.
    The 'order' field maintains the preferred ordering of definitions.
    """

    __tablename__ = "definitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    word_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("words.id", ondelete="CASCADE"), nullable=False, index=True
    )
    definition_text: Mapped[str] = mapped_column(Text, nullable=False)
    part_of_speech: Mapped[PartOfSpeech] = mapped_column(
        SQLEnum(PartOfSpeech, native_enum=False, length=50), nullable=False
    )
    order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )  # For ordering multiple definitions

    # Relationships
    word: Mapped[Word] = relationship("Word", back_populates="definitions")
    examples: Mapped[list[Example]] = relationship(
        "Example",
        back_populates="definition",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        # Ensure unique (word_id, order) to prevent duplicate orders
        UniqueConstraint("word_id", "order", name="uq_word_definition_order"),
        # Index for full-text search on definitions
        Index("idx_definition_text", "definition_text"),
    )

    def __repr__(self) -> str:
        return f"<Definition(id={self.id}, word_id={self.word_id}, pos='{self.part_of_speech}')>"


class Example(Base):
    """Usage examples for definitions.

    Multiple examples can be associated with each definition.
    Source attribution (e.g., 'Shakespeare, Hamlet') is optional.
    """

    __tablename__ = "examples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    definition_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    example_text: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # Optional source attribution

    # Relationships
    definition: Mapped[Definition] = relationship(
        "Definition", back_populates="examples"
    )

    __table_args__ = (Index("idx_example_text", "example_text"),)

    def __repr__(self) -> str:
        return f"<Example(id={self.id}, definition_id={self.definition_id})>"


class WordRelation(Base):
    """Self-referential relationships between words.

    Links two words with a specific relationship type (synonym, antonym, etc.).
    Note: Relations are directional (word1 -> word2).
    """

    __tablename__ = "word_relations"

    word_id_1: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("words.id", ondelete="CASCADE"),
        primary_key=True,
    )
    word_id_2: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("words.id", ondelete="CASCADE"),
        primary_key=True,
    )
    relation_type: Mapped[RelationType] = mapped_column(
        SQLEnum(RelationType, native_enum=False, length=50),
        nullable=False,
        index=True,
    )

    # Relationships to the Word model
    word_1: Mapped[Word] = relationship(
        "Word",
        foreign_keys=[word_id_1],
    )
    word_2: Mapped[Word] = relationship(
        "Word",
        foreign_keys=[word_id_2],
    )

    __table_args__ = (
        # Prevent self-relations (word cannot be related to itself)
        CheckConstraint("word_id_1 != word_id_2", name="ck_no_self_relation"),
        # Index for efficient lookups
        Index("idx_word_relation", "word_id_1", "word_id_2", "relation_type"),
    )

    def __repr__(self) -> str:
        return f"<WordRelation({self.word_id_1} --{self.relation_type}--> {self.word_id_2})>"


class Tag(Base):
    """Topics/categories for organizing words.

    Examples: 'medical', 'legal', 'informal', 'archaic', etc.
    """

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    words: Mapped[list[Word]] = relationship(
        "Word",
        secondary="word_tags",
        back_populates="tags",
    )

    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, name='{self.name}')>"


class WordTag(Base):
    """Junction table for many-to-many relationship between Words and Tags."""

    __tablename__ = "word_tags"

    word_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("words.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    )

    __table_args__ = (
        # Index for efficient lookups
        Index("idx_word_tag", "word_id", "tag_id"),
    )

    def __repr__(self) -> str:
        return f"<WordTag(word_id={self.word_id}, tag_id={self.tag_id})>"


class WordForm(Base):
    """Word inflections and variants (following Oxford Dictionary approach).

    Stores all forms of a word (defying, defied, defies) that point to
    the headword entry (defy). Enables search by any form to find the main entry.
    """

    __tablename__ = "word_forms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    word_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("words.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    form_text: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )  # e.g., "defying", "defied"
    form_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # e.g., "present_participle", "past_tense"

    # Relationships
    word: Mapped[Word] = relationship("Word", back_populates="word_forms")

    __table_args__ = (
        # Ensure unique (form_text, word_id) - same form can't be added twice to same word
        UniqueConstraint("word_id", "form_text", name="uq_word_form"),
        # Index for fast lookup by form text
        Index("idx_form_text", "form_text"),
    )

    def __repr__(self) -> str:
        return (
            f"<WordForm(id={self.id}, form='{self.form_text}', word_id={self.word_id})>"
        )


# ============================================================================
# Event Listeners - Auto-update Word.updated_at on nested data changes
# ============================================================================


def _update_word_timestamp(word_id: int, connection: object) -> None:
    """Update Word.updated_at timestamp efficiently."""
    # Use update() for efficiency - avoids loading the full Word object
    from sqlalchemy import update

    stmt = update(Word).where(Word.id == word_id).values(updated_at=datetime.now(UTC))
    connection.execute(stmt)  # type: ignore[attr-defined]


# Definition events - update parent Word timestamp
@event.listens_for(Definition, "after_insert")
@event.listens_for(Definition, "after_update")
@event.listens_for(Definition, "after_delete")
def _update_word_on_definition_change(  # pyright: ignore[reportUnusedFunction]
    mapper: object, connection: object, target: Definition
) -> None:  # noqa: ARG001
    """Update parent Word timestamp when definition changes."""
    _update_word_timestamp(target.word_id, connection)


# Example events - update grandparent Word timestamp via Definition
@event.listens_for(Example, "after_insert")
@event.listens_for(Example, "after_update")
@event.listens_for(Example, "after_delete")
def _update_word_on_example_change(  # pyright: ignore[reportUnusedFunction]
    mapper: object, connection: object, target: Example
) -> None:  # noqa: ARG001
    """Update grandparent Word timestamp when example changes."""
    # Get the parent definition's word_id
    from sqlalchemy import select

    stmt = select(Definition.word_id).where(Definition.id == target.definition_id)
    result = connection.execute(stmt)  # type: ignore[attr-defined]
    row = result.fetchone()
    if row:
        _update_word_timestamp(row[0], connection)


# WordTag events - update parent Word timestamp
@event.listens_for(WordTag, "after_insert")
@event.listens_for(WordTag, "after_delete")
def _update_word_on_tag_change(  # pyright: ignore[reportUnusedFunction]
    mapper: object, connection: object, target: WordTag
) -> None:  # noqa: ARG001
    """Update parent Word timestamp when tags change."""
    _update_word_timestamp(target.word_id, connection)
