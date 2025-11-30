"""Pydantic schemas for API request/response validation.

Includes schemas for:
- Inference: prediction and activation endpoints
- Dictionary: word, definition, example, tag, and relation models
"""

from schemas.common import HealthCheck
from schemas.dictionary import (
    DefinitionNested,
    DefinitionOut,
    ExampleBase,
    ExampleOut,
    PaginatedRelations,
    PaginatedTags,
    PaginatedWords,
    RelationCreate,
    RelationOut,
    TagCreate,
    TagOut,
    TagUpdate,
    WordCreate,
    WordFull,
    WordOut,
    WordUpdate,
)
from schemas.inference import (
    ActivationsInput,
    ActivationsOutput,
    PredictionInput,
    PredictionOutput,
)

__all__ = [
    "ActivationsInput",
    "ActivationsOutput",
    # Dictionary - Definitions
    "DefinitionNested",
    "DefinitionOut",
    # Dictionary - Examples
    "ExampleBase",
    "ExampleOut",
    # Common
    "HealthCheck",
    "PaginatedRelations",
    "PaginatedTags",
    "PaginatedWords",
    # Inference
    "PredictionInput",
    "PredictionOutput",
    # Dictionary - Relations
    "RelationCreate",
    "RelationOut",
    # Dictionary - Tags
    "TagCreate",
    "TagOut",
    "TagUpdate",
    # Dictionary - Words
    "WordCreate",
    "WordFull",
    "WordOut",
    "WordUpdate",
]
