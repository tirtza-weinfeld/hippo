"""Global application state."""

from neural_networks import NeuralNetwork, DataPair


class AppState:
    """Application state container."""

    network: NeuralNetwork | None = None
    training_data: list[DataPair] = []
    validation_data: list[DataPair] = []
    test_data: list[DataPair] = []
    mnist_loaded: bool = False
    is_training: bool = False


# Global state instance
state = AppState()
