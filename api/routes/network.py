"""Neural network API routes."""

import asyncio
import json
from typing import AsyncGenerator

import numpy as np
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from api.state import state
from neural_networks import NeuralNetwork
from schemas import (
    ActivationsInput,
    ActivationsOutput,
    NetworkCreate,
    NetworkState,
    PredictionInput,
    PredictionOutput,
    TrainingConfig,
    TrainingProgress,
)


router = APIRouter(prefix="/network", tags=["network"])


@router.post("/create", response_model=NetworkState, status_code=201)
def create_network(config: NetworkCreate) -> NetworkState:
    """Create a new neural network with specified architecture.

    Args:
        config: Network configuration

    Returns:
        Created network state

    Raises:
        HTTPException: If network creation fails or training in progress
    """
    if state.is_training:
        raise HTTPException(
            status_code=409,
            detail="Cannot create network while training is in progress",
        )

    try:
        state.network = NeuralNetwork(
            sizes=config.sizes,
            activation=config.activation,
        )
        return NetworkState(**state.network.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/state", response_model=NetworkState)
def get_network_state() -> NetworkState:
    """Get current network state (weights, biases, config).

    Returns:
        Current network state

    Raises:
        HTTPException: If no network exists
    """
    if state.network is None:
        raise HTTPException(
            status_code=404,
            detail="No network created. Use POST /network/create first",
        )
    return NetworkState(**state.network.to_dict())


@router.post("/train")
async def train_network(config: TrainingConfig) -> StreamingResponse:
    """Train the neural network on MNIST data with streaming progress.

    Args:
        config: Training configuration

    Returns:
        Server-sent events stream with training progress

    Raises:
        HTTPException: If network doesn't exist, MNIST not loaded, or already training
    """
    if state.network is None:
        raise HTTPException(
            status_code=404,
            detail="No network created. Use POST /network/create first",
        )

    if not state.mnist_loaded:
        raise HTTPException(
            status_code=503,
            detail="MNIST data not loaded",
        )

    if state.is_training:
        raise HTTPException(
            status_code=409,
            detail="Training already in progress",
        )

    async def train_with_progress() -> AsyncGenerator[str, None]:
        """Train network and yield progress updates."""
        state.is_training = True
        try:
            test_data = state.test_data if config.use_test_data else None
            n = len(state.training_data)

            for epoch in range(config.epochs):
                # Shuffle and create mini-batches
                np.random.shuffle(state.training_data)
                mini_batches = [
                    state.training_data[k:k + config.mini_batch_size]
                    for k in range(0, n, config.mini_batch_size)
                ]

                # Train on mini-batches
                for mini_batch in mini_batches:
                    state.network._update_mini_batch(mini_batch, config.learning_rate)
                    # Yield control to event loop periodically
                    await asyncio.sleep(0)

                # Evaluate and send progress
                progress = TrainingProgress(
                    epoch=epoch + 1,
                    total_epochs=config.epochs,
                )

                if test_data is not None:
                    accuracy = state.network.evaluate(test_data)
                    progress.test_accuracy = accuracy
                    progress.test_total = len(test_data)
                    progress.accuracy_percent = (accuracy / len(test_data)) * 100

                # Send progress as JSON
                yield f"data: {progress.model_dump_json()}\n\n"

            # Send completion message
            yield 'data: {"status": "completed"}\n\n'

        finally:
            state.is_training = False

    return StreamingResponse(
        train_with_progress(),
        media_type="text/event-stream",
    )


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
            status_code=404,
            detail="No network created. Use POST /network/create first",
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
            status_code=404,
            detail="No network created. Use POST /network/create first",
        )

    try:
        x = np.array(input_data.pixels, dtype=np.float64).reshape(784, 1)
        activations = state.network.get_all_activations(x)

        return ActivationsOutput(
            activations=[act.flatten().tolist() for act in activations],
            layer_sizes=state.network.sizes,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get activations: {e}") from e
