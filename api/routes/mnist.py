"""MNIST dataset API routes."""

from fastapi import APIRouter, HTTPException

from api.state import state
from neural_networks import get_random_samples
from schemas import MNISTSamples


router = APIRouter(prefix="/mnist", tags=["mnist"])


@router.get("/samples", response_model=MNISTSamples)
def get_mnist_samples(count: int = 10, dataset: str = "test") -> MNISTSamples:
    """Get random MNIST samples for testing/visualization.

    Args:
        count: Number of samples to return (max 100)
        dataset: Which dataset to sample from ("train", "validation", "test")

    Returns:
        Random MNIST samples

    Raises:
        HTTPException: If MNIST not loaded or invalid parameters
    """
    if not state.mnist_loaded:
        raise HTTPException(status_code=503, detail="MNIST data not loaded")

    if count < 1 or count > 100:
        raise HTTPException(status_code=400, detail="Count must be between 1 and 100")

    match dataset:
        case "train":
            data = state.training_data
        case "validation":
            data = state.validation_data
        case "test":
            data = state.test_data
        case _:
            raise HTTPException(
                status_code=400,
                detail="Invalid dataset. Use 'train', 'validation', or 'test'",
            )

    samples = get_random_samples(data, count)
    return MNISTSamples(samples=samples, count=len(samples))
