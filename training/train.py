"""Pure training logic for neural networks.

Clean, importable functions without CLI dependencies.
Can be used in Jupyter notebooks, tests, or other scripts.
"""

import json
import sys
from pathlib import Path
from typing import Any, Literal

import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from neural_networks.core import NeuralNetwork
from neural_networks.mnist_loader import MNISTLoader


def train_network(
    sizes: list[int],
    activation: Literal["sigmoid", "relu"],
    epochs: int,
    learning_rate: float,
    mini_batch_size: int = 10,
    seed: int | None = None,
) -> tuple[NeuralNetwork, float]:
    """Train a neural network on MNIST dataset.

    Args:
        sizes: Layer architecture (e.g., [784, 100, 10])
        activation: Activation function ('sigmoid' or 'relu')
        epochs: Number of training epochs
        learning_rate: Learning rate for gradient descent
        mini_batch_size: Mini-batch size for SGD
        seed: Random seed for reproducibility (optional)

    Returns:
        Tuple of (trained network, final accuracy percentage)
    """
    # Set random seed if provided
    if seed is not None:
        np.random.seed(seed)

    # Load MNIST data
    training_data, validation_data, test_data = MNISTLoader.load_data()

    # Create network
    network = NeuralNetwork(sizes=sizes, activation=activation)

    # Train
    network.train(
        training_data=training_data,
        epochs=epochs,
        mini_batch_size=mini_batch_size,
        learning_rate=learning_rate,
        test_data=test_data,
    )

    # Evaluate final accuracy
    final_accuracy_count = network.evaluate(test_data)
    final_accuracy_percent = (final_accuracy_count / len(test_data)) * 100

    return network, final_accuracy_percent


def save_model(
    network: NeuralNetwork,
    filepath: Path,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Save trained model to .npz and .json files (HuggingFace compatible).

    Model parameters are saved to .npz file with individual arrays per layer.
    Metadata is saved to separate .json file for clarity and compatibility.

    Args:
        network: Trained neural network
        filepath: Output file path (.npz) - metadata will be saved as .json
        metadata: Optional metadata dictionary (training config, metrics, etc.)
    """
    # Ensure parent directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Prepare model data with individual arrays per layer
    # This avoids inhomogeneous shape errors and is cleaner
    save_data: dict[str, Any] = {
        "sizes": np.array(network.sizes),
        "activation": network.activation_name,
        "num_layers": network.num_layers,
    }

    # Save each weight and bias matrix individually
    for i, weight in enumerate(network.weights):
        save_data[f"weight_{i}"] = weight

    for i, bias in enumerate(network.biases):
        save_data[f"bias_{i}"] = bias

    # Save model parameters as compressed NumPy archive
    np.savez_compressed(filepath, **save_data)

    # Save metadata to separate JSON file if provided
    if metadata:
        metadata_path = filepath.with_suffix(".json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)


def load_model(filepath: Path) -> tuple[NeuralNetwork, dict[str, Any] | None]:
    """Load trained model from .npz file.

    Args:
        filepath: Path to model file (.npz)

    Returns:
        Tuple of (network, metadata_dict or None)

    Raises:
        FileNotFoundError: If model file doesn't exist
        ValueError: If model format is invalid
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Model file not found: {filepath}")

    # Load model data
    data = np.load(filepath)

    # Extract architecture
    sizes = data["sizes"].tolist()
    activation = str(data["activation"])
    num_layers = int(data["num_layers"])

    # Reconstruct weights and biases from individual arrays
    weights = [data[f"weight_{i}"] for i in range(num_layers - 1)]
    biases = [data[f"bias_{i}"] for i in range(num_layers - 1)]

    # Create network with loaded parameters
    network_dict: dict[str, Any] = {
        "sizes": sizes,
        "activation": activation,
        "weights": weights,
        "biases": biases,
    }

    network = NeuralNetwork.from_dict(network_dict)

    # Load metadata if available
    metadata = None
    metadata_path = filepath.with_suffix(".json")
    if metadata_path.exists():
        with open(metadata_path) as f:
            metadata = json.load(f)

    return network, metadata
