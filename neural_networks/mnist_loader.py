"""MNIST dataset loader for neural network training.

Downloads and processes MNIST handwritten digit dataset.
"""

from pathlib import Path
import gzip
import pickle
from typing import TypeAlias
import urllib.request

import numpy as np
import numpy.typing as npt


NDArrayFloat = npt.NDArray[np.floating]
NDArrayInt = npt.NDArray[np.int_]
DataPair: TypeAlias = tuple[NDArrayFloat, NDArrayFloat]


class MNISTLoader:
    """Handler for MNIST dataset download and processing."""

    MNIST_URL = "https://github.com/mnielsen/neural-networks-and-deep-learning/raw/master/data/mnist.pkl.gz"
    DATA_DIR = Path("data")
    MNIST_FILE = DATA_DIR / "mnist.pkl.gz"

    @classmethod
    def load_data(cls) -> tuple[list[DataPair], list[DataPair], list[DataPair]]:
        """Load MNIST dataset, downloading if necessary.

        Returns:
            Tuple of (training_data, validation_data, test_data)
            Each is a list of (input, label) pairs where:
            - input is (784, 1) array of pixel values [0, 1]
            - label is (10, 1) one-hot encoded vector for training/validation
            - label is integer for test data

        Raises:
            RuntimeError: If download or processing fails
        """
        if not cls.MNIST_FILE.exists():
            cls._download_mnist()

        try:
            with gzip.open(cls.MNIST_FILE, "rb") as f:
                training_data, validation_data, test_data = pickle.load(f, encoding="latin1")
        except Exception as e:
            raise RuntimeError(f"Failed to load MNIST data: {e}") from e

        return (
            cls._format_training_data(training_data),
            cls._format_training_data(validation_data),
            cls._format_test_data(test_data),
        )

    @classmethod
    def _download_mnist(cls) -> None:
        """Download MNIST dataset from repository.

        Raises:
            RuntimeError: If download fails
        """
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)

        try:
            urllib.request.urlretrieve(cls.MNIST_URL, cls.MNIST_FILE)
        except Exception as e:
            raise RuntimeError(f"Failed to download MNIST: {e}") from e

    @staticmethod
    def _format_training_data(
        data: tuple[NDArrayFloat, NDArrayInt],
    ) -> list[DataPair]:
        """Format data for training with one-hot encoded labels.

        Args:
            data: Tuple of (inputs, labels) where inputs are (n, 784) and labels are (n,)

        Returns:
            List of (input, one_hot_label) pairs
        """
        inputs, labels = data
        formatted_inputs = [
            np.reshape(x, (784, 1)).astype(np.float64) for x in inputs
        ]
        formatted_labels = [
            _vectorize_label(y) for y in labels
        ]
        return list(zip(formatted_inputs, formatted_labels))

    @staticmethod
    def _format_test_data(
        data: tuple[NDArrayFloat, NDArrayInt],
    ) -> list[DataPair]:
        """Format test data with one-hot encoded labels for consistency.

        Args:
            data: Tuple of (inputs, labels)

        Returns:
            List of (input, one_hot_label) pairs
        """
        inputs, labels = data
        formatted_inputs = [
            np.reshape(x, (784, 1)).astype(np.float64) for x in inputs
        ]
        formatted_labels = [
            _vectorize_label(y) for y in labels
        ]
        return list(zip(formatted_inputs, formatted_labels))


def _vectorize_label(j: int) -> NDArrayFloat:
    """Convert digit to one-hot encoded vector.

    Args:
        j: Digit (0-9)

    Returns:
        One-hot encoded (10, 1) vector
    """
    e = np.zeros((10, 1), dtype=np.float64)
    e[j] = 1.0
    return e


def get_random_samples(
    data: list[DataPair],
    count: int = 10,
) -> list[dict[str, list[float] | int]]:
    """Get random samples from dataset for visualization.

    Args:
        data: Dataset to sample from
        count: Number of samples to return

    Returns:
        List of dicts with 'pixels' and 'label' keys
    """
    indices = np.random.choice(len(data), size=min(count, len(data)), replace=False)
    samples: list[dict[str, list[float] | int]] = []

    for idx in indices:
        x, y = data[int(idx)]
        label = int(np.argmax(y))
        pixels = x.flatten().tolist()
        samples.append({"pixels": pixels, "label": label})

    return samples
