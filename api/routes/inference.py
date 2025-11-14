"""Inference API routes for neural network predictions."""

import numpy as np
from fastapi import APIRouter, HTTPException

from api.state import state
from schemas.inference import (
    ActivationsInput,
    ActivationsOutput,
    PredictionInput,
    PredictionOutput,
)


router = APIRouter(tags=["inference"])


@router.post("/predict", response_model=PredictionOutput)
def predict(input_data: PredictionInput) -> PredictionOutput:
    """Get network prediction for input image.

    Args:
        input_data: Input pixels (784-dimensional)

    Returns:
        Prediction with confidence scores

    Raises:
        HTTPException: If network doesn't exist
    """
    if state.network is None:
        raise HTTPException(
            status_code=503,
            detail="No model loaded. Check server configuration.",
        )

    try:
        x = np.array(input_data.pixels, dtype=np.float64).reshape(784, 1)
        output = state.network.feedforward(x)

        probabilities = output.flatten().tolist()
        predicted_digit = int(np.argmax(output))
        confidence = float(output[predicted_digit, 0])

        return PredictionOutput(
            predicted_digit=predicted_digit,
            confidence=confidence,
            probabilities=probabilities,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}") from e


@router.post("/activations", response_model=ActivationsOutput)
def get_activations(input_data: ActivationsInput) -> ActivationsOutput:
    """Get all layer activations for visualization.

    Args:
        input_data: Input pixels

    Returns:
        Activations for all layers

    Raises:
        HTTPException: If network doesn't exist
    """
    if state.network is None:
        raise HTTPException(
            status_code=503,
            detail="No model loaded. Check server configuration.",
        )

    try:
        x = np.array(input_data.pixels, dtype=np.float64).reshape(784, 1)
        activations = state.network.get_all_activations(x)

        return ActivationsOutput(
            activations=[act.flatten().tolist() for act in activations],
            layer_sizes=state.network.sizes,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get activations: {e}"
        ) from e
