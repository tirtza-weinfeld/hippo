"""Pydantic schemas for neural network operations."""

from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class NetworkCreate(BaseModel):
    """Request to create a new neural network."""

    sizes: list[int] = Field(
        min_length=2,
        description="Layer sizes (e.g., [784, 30, 10] for MNIST)",
        examples=[[784, 30, 10]],
    )
    activation: Literal["sigmoid", "relu"] = Field(
        default="sigmoid",
        description="Activation function",
    )


class NetworkState(BaseModel):
    """Current state of neural network."""

    sizes: list[int]
    activation: str
    weights: list[list[list[float]]]
    biases: list[list[list[float]]]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sizes": [784, 30, 10],
                "activation": "sigmoid",
                "weights": [[[0.1, -0.2]], [[0.3, 0.4]]],
                "biases": [[[0.1]], [[0.2]]],
            }
        }
    )


class TrainingConfig(BaseModel):
    """Configuration for training session."""

    epochs: int = Field(gt=0, le=100, description="Number of training epochs")
    mini_batch_size: int = Field(
        default=10,
        gt=0,
        le=1000,
        description="Mini-batch size for SGD",
    )
    learning_rate: float = Field(
        default=3.0,
        gt=0,
        le=10.0,
        description="Learning rate (eta)",
    )
    use_test_data: bool = Field(
        default=True,
        description="Evaluate on test data after each epoch",
    )


class TrainingProgress(BaseModel):
    """Real-time training progress update."""

    epoch: int
    total_epochs: int
    test_accuracy: int | None = None
    test_total: int | None = None
    accuracy_percent: float | None = None


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
