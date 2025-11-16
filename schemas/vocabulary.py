"""Pydantic schemas for vocabulary API.

These schemas define the request/response models for the vocabulary endpoints.
Follows the Create/Update/Out pattern for data validation.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from db.models.vocabulary import PartOfSpeech, RelationType


# ============================================================================
# Example Schemas
# ============================================================================


class ExampleBase(BaseModel):
    """Base schema for examples."""

    example_text: str = Field(
        ..., min_length=1, max_length=5000, description="Usage example sentence"
    )
    source: str | None = Field(
        None,
        max_length=255,
        description="Source attribution (e.g., 'Shakespeare, Hamlet')",
    )


class ExampleCreate(ExampleBase):
    """Schema for creating a new example."""

    definition_id: int = Field(..., gt=0)


class ExampleUpdate(BaseModel):
    """Schema for updating an existing example."""

    example_text: str | None = Field(None, min_length=1, max_length=5000)
    source: str | None = Field(None, max_length=255)


class ExampleOut(ExampleBase):
    """Schema for example response."""

    id: int
    definition_id: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Definition Schemas
# ============================================================================


class DefinitionBase(BaseModel):
    """Base schema for definitions."""

    definition_text: str = Field(..., min_length=1, max_length=10000)
    part_of_speech: PartOfSpeech = Field(
        ..., description="Grammatical category of the word"
    )
    order: int = Field(
        default=0, ge=0, description="Order of this definition (0 is first)"
    )


class DefinitionCreate(DefinitionBase):
    """Schema for creating a new definition."""

    word_id: int = Field(..., gt=0)


class DefinitionUpdate(BaseModel):
    """Schema for updating an existing definition."""

    definition_text: str | None = Field(None, min_length=1, max_length=10000)
    part_of_speech: PartOfSpeech | None = Field(
        None, description="Grammatical category of the word"
    )
    order: int | None = Field(None, ge=0, description="Order of this definition")


class DefinitionOut(DefinitionBase):
    """Schema for definition response (without nested examples)."""

    id: int
    word_id: int

    model_config = ConfigDict(from_attributes=True)


class DefinitionWithExamples(DefinitionOut):
    """Schema for definition with nested examples."""

    examples: list[ExampleOut] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Word Schemas
# ============================================================================


class WordBase(BaseModel):
    """Base schema for words."""

    word_text: str = Field(
        ..., min_length=1, max_length=255, description="The word itself"
    )
    language_code: str = Field(
        ...,
        min_length=2,
        max_length=10,
        description="ISO language code (e.g., 'en', 'es', 'fr')",
    )


class WordCreate(WordBase):
    """Schema for creating a new word."""

    pass


class WordUpdate(BaseModel):
    """Schema for updating an existing word."""

    word_text: str | None = Field(None, min_length=1, max_length=255)
    language_code: str | None = Field(None, min_length=2, max_length=10)


class WordOut(WordBase):
    """Schema for word response (without nested data)."""

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WordWithDefinitions(WordOut):
    """Schema for word with nested definitions (but not examples)."""

    definitions: list[DefinitionOut] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class WordFull(WordOut):
    """Schema for word with full nested data (definitions + examples)."""

    definitions: list[DefinitionWithExamples] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Word Relation Schemas
# ============================================================================


class WordRelationBase(BaseModel):
    """Base schema for word relations."""

    word_id_1: int = Field(..., gt=0, description="First word ID")
    word_id_2: int = Field(..., gt=0, description="Second word ID")
    relation_type: RelationType = Field(
        ..., description="Type of relationship (synonym, antonym, etc.)"
    )


class WordRelationCreate(WordRelationBase):
    """Schema for creating a word relation."""

    pass


class WordRelationOut(WordRelationBase):
    """Schema for word relation response."""

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Tag Schemas
# ============================================================================


class TagBase(BaseModel):
    """Base schema for tags."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Tag name (e.g., 'medical', 'informal', 'archaic')",
    )
    description: str | None = Field(
        None, max_length=1000, description="Optional description of the tag"
    )


class TagCreate(TagBase):
    """Schema for creating a new tag."""

    pass


class TagUpdate(BaseModel):
    """Schema for updating an existing tag."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=1000)


class TagOut(TagBase):
    """Schema for tag response."""

    id: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Word-Tag Junction Schemas
# ============================================================================


class WordTagCreate(BaseModel):
    """Schema for creating a word-tag association."""

    word_id: int = Field(..., gt=0)
    tag_id: int = Field(..., gt=0)


class WordTagOut(BaseModel):
    """Schema for word-tag association response."""

    word_id: int
    tag_id: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Composite Schemas for Complex Queries
# ============================================================================


class WordWithTags(WordOut):
    """Schema for word with associated tags."""

    tags: list[TagOut] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class TagWithWords(TagOut):
    """Schema for tag with associated words."""

    words: list[WordOut] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
