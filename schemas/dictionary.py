"""Pydantic schemas for dictionary API.

Clean, modern schemas supporting nested data operations.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from db.models.dictionary import PartOfSpeech, RelationType

# ============================================================================
# Example Schemas
# ============================================================================


class ExampleBase(BaseModel):
    """Base schema for examples."""

    example_text: str = Field(..., min_length=1, max_length=5000)
    source: str | None = Field(None, max_length=255)


class ExampleOut(ExampleBase):
    """Example response schema."""

    id: int
    definition_id: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Definition Schemas
# ============================================================================


class DefinitionNested(BaseModel):
    """Definition with nested examples (for create/update)."""

    id: int | None = Field(None, description="ID when updating, omit when creating")
    definition_text: str = Field(..., min_length=1, max_length=10000)
    part_of_speech: PartOfSpeech
    order: int = Field(default=0, ge=0)
    examples: list[ExampleBase] = Field(default_factory=list)


class DefinitionOut(BaseModel):
    """Definition response schema."""

    id: int
    word_id: int
    definition_text: str
    part_of_speech: PartOfSpeech
    order: int
    examples: list[ExampleOut] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Word Form Schemas (Oxford approach - inflections)
# ============================================================================


class WordFormBase(BaseModel):
    """Base schema for word forms."""

    form_text: str = Field(..., min_length=1, max_length=255)
    form_type: str | None = Field(None, max_length=50)


class WordFormOut(WordFormBase):
    """Word form response schema."""

    id: int
    word_id: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Word Schemas
# ============================================================================


class WordCreate(BaseModel):
    """Word creation schema - supports nested data."""

    word_text: str = Field(..., min_length=1, max_length=255)
    language_code: str = Field(..., min_length=2, max_length=10)
    definitions: list[DefinitionNested] = Field(default_factory=list)
    tags: list[str] = Field(
        default_factory=list, description="Tag names (auto-created if they don't exist)"
    )
    word_forms: list[WordFormBase] = Field(
        default_factory=list, description="Inflections (defying, defied, etc.)"
    )


class WordUpdate(BaseModel):
    """Word update schema - all fields optional, supports nested data."""

    word_text: str | None = Field(None, min_length=1, max_length=255)
    language_code: str | None = Field(None, min_length=2, max_length=10)
    definitions: list[DefinitionNested] | None = None
    tags: list[str] | None = Field(
        None, description="Tag names (auto-created if they don't exist)"
    )
    word_forms: list[WordFormBase] | None = Field(
        None, description="Inflections (defying, defied, etc.)"
    )


class WordOut(BaseModel):
    """Word response schema (simple - no nested data)."""

    id: int
    word_text: str
    language_code: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Tag Schemas
# ============================================================================


class TagCreate(BaseModel):
    """Tag creation schema."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=1000)


class TagUpdate(BaseModel):
    """Tag update schema."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=1000)


class TagOut(BaseModel):
    """Tag response schema."""

    id: int
    name: str
    description: str | None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Word Full Schema (needs TagOut defined first)
# ============================================================================


class WordFull(BaseModel):
    """Word response schema (full - with all nested data)."""

    id: int
    word_text: str
    language_code: str
    created_at: datetime
    updated_at: datetime
    definitions: list[DefinitionOut] = Field(default_factory=list)
    tags: list[TagOut] = Field(default_factory=list)
    word_forms: list[WordFormOut] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Relation Schemas
# ============================================================================


class RelationCreate(BaseModel):
    """Word relation creation schema."""

    word_id_1: int = Field(..., gt=0)
    word_id_2: int = Field(..., gt=0)
    relation_type: RelationType


class RelationOut(BaseModel):
    """Word relation response schema."""

    word_id_1: int
    word_id_2: int
    relation_type: RelationType

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Paginated Response Schemas
# ============================================================================


class PaginatedResponse[T](BaseModel):
    """Generic paginated response."""

    data: list[T]
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    total_pages: int = Field(..., ge=0)
    has_more: bool

    model_config = ConfigDict(from_attributes=True)


# Type aliases for specific paginated responses
PaginatedWords = PaginatedResponse[WordOut]
PaginatedTags = PaginatedResponse[TagOut]
PaginatedRelations = PaginatedResponse[RelationOut]
