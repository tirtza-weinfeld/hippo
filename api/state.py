"""Global application state."""

from neural_networks import NeuralNetwork


class AppState:
    """Application state container.

    Holds the loaded model from HF Hub for inference.
    """

    network: NeuralNetwork | None = None


# Global state instance
state = AppState()
