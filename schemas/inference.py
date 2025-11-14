"""Pydantic schemas for inference operations."""

from pydantic import BaseModel, Field


class PredictionInput(BaseModel):
    """Input for network prediction."""

    pixels: list[float] = Field(
        min_length=784,
        max_length=784,
        description="Flattened 28x28 image (784 pixels), normalized [0, 1]",
    )


class PredictionOutput(BaseModel):
    """Network prediction output."""

    predicted_digit: int = Field(ge=0, le=9)
    confidence: float = Field(ge=0.0, le=1.0)
    probabilities: list[float] = Field(min_length=10, max_length=10)


class ActivationsInput(BaseModel):
    """Input for getting all layer activations."""

    pixels: list[float] = Field(
        min_length=784,
        max_length=784,
        description="Flattened 28x28 image",
    )


class ActivationsOutput(BaseModel):
    """All layer activations for visualization."""

    activations: list[list[float]] = Field(
        description="Activation values for each layer",
    )
    layer_sizes: list[int]
