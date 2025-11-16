"""Pydantic schemas for API request/response validation.

Includes schemas for:
- Inference: prediction and activation endpoints
- Vocabulary: word, definition, example, tag, and relation models
"""

from schemas.common import HealthCheck
from schemas.inference import (
    ActivationsInput,
    ActivationsOutput,
    PredictionInput,
    PredictionOutput,
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
    WordTagCreate,
    WordTagOut,
    WordUpdate,
    WordWithDefinitions,
    WordWithTags,
)

__all__ = [
    # Common
    "HealthCheck",
    # Inference
    "PredictionInput",
    "PredictionOutput",
    "ActivationsInput",
    "ActivationsOutput",
    # Vocabulary - Words
    "WordCreate",
    "WordUpdate",
    "WordOut",
    "WordWithDefinitions",
    "WordFull",
    "WordWithTags",
    # Vocabulary - Definitions
    "DefinitionCreate",
    "DefinitionUpdate",
    "DefinitionOut",
    "DefinitionWithExamples",
    # Vocabulary - Examples
    "ExampleCreate",
    "ExampleUpdate",
    "ExampleOut",
    # Vocabulary - Relations
    "WordRelationCreate",
    "WordRelationOut",
    # Vocabulary - Tags
    "TagCreate",
    "TagUpdate",
    "TagOut",
    "TagWithWords",
    # Vocabulary - Word-Tag Junction
    "WordTagCreate",
    "WordTagOut",
]
