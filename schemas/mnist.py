"""Pydantic schemas for MNIST operations."""

from pydantic import BaseModel, Field


class MNISTSample(BaseModel):
    """Single MNIST sample."""

    pixels: list[float] = Field(min_length=784, max_length=784)
    label: int = Field(ge=0, le=9)


class MNISTSamples(BaseModel):
    """Collection of MNIST samples."""

    samples: list[MNISTSample]
    count: int
