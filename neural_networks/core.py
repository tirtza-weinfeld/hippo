"""Neural Network implementation following 3Blue1Brown tutorial.

Modern Python 3.14+ implementation with NumPy for learning purposes.
"""

from typing import Literal
import numpy as np
import numpy.typing as npt


NDArrayFloat = npt.NDArray[np.floating]


class NeuralNetwork:
    """Feedforward neural network with backpropagation.

    Implements the neural network described in 3Blue1Brown's series:
    - Configurable layer sizes
    - Sigmoid or ReLU activation
    - Stochastic gradient descent training
    - Backpropagation for computing gradients
    """

    def __init__(
        self,
        sizes: list[int],
        activation: Literal["sigmoid", "relu"] = "sigmoid",
    ) -> None:
        """Initialize network with random weights and biases.

        Args:
            sizes: List of layer sizes (e.g., [784, 30, 10] for MNIST)
            activation: Activation function to use

        Raises:
            ValueError: If sizes has fewer than 2 layers
        """
        if len(sizes) < 2:
            raise ValueError("Network must have at least 2 layers")

        self.num_layers: int = len(sizes)
        self.sizes: list[int] = sizes
        self.activation_name: Literal["sigmoid", "relu"] = activation

        # Initialize biases for all layers except input
        self.biases: list[NDArrayFloat] = [
            np.random.randn(y, 1).astype(np.float64) for y in sizes[1:]
        ]

        # Initialize weights with Gaussian distribution
        self.weights: list[NDArrayFloat] = [
            np.random.randn(y, x).astype(np.float64)
            for x, y in zip(sizes[:-1], sizes[1:])
        ]

    def feedforward(self, a: NDArrayFloat) -> NDArrayFloat:
        """Compute network output for given input.

        Args:
            a: Input vector (n, 1) where n is input layer size

        Returns:
            Output activations (m, 1) where m is output layer size
        """
        for b, w in zip(self.biases, self.weights):
            z = w @ a + b
            a = self._activation(z)
        return a

    def get_all_activations(self, a: NDArrayFloat) -> list[NDArrayFloat]:
        """Get activations for all layers (useful for visualization).

        Args:
            a: Input vector (n, 1)

        Returns:
            List of activation arrays for each layer
        """
        activations: list[NDArrayFloat] = [a]
        for b, w in zip(self.biases, self.weights):
            z = w @ activations[-1] + b
            a = self._activation(z)
            activations.append(a)
        return activations

    def train(
        self,
        training_data: list[tuple[NDArrayFloat, NDArrayFloat]],
        epochs: int,
        mini_batch_size: int,
        learning_rate: float,
        test_data: list[tuple[NDArrayFloat, NDArrayFloat]] | None = None,
    ) -> list[dict[str, int | float]]:
        """Train network using mini-batch stochastic gradient descent.

        Args:
            training_data: List of (input, target) tuples
            epochs: Number of training epochs
            mini_batch_size: Size of mini-batches
            learning_rate: Learning rate (eta)
            test_data: Optional test data for evaluation

        Returns:
            Training history with epoch metrics
        """
        n = len(training_data)
        history: list[dict[str, int | float]] = []

        for epoch in range(epochs):
            # Shuffle and create mini-batches
            np.random.shuffle(training_data)
            mini_batches = [
                training_data[k:k + mini_batch_size]
                for k in range(0, n, mini_batch_size)
            ]

            # Update network on each mini-batch
            for mini_batch in mini_batches:
                self._update_mini_batch(mini_batch, learning_rate)

            # Evaluate and record metrics
            metrics: dict[str, int | float] = {"epoch": epoch + 1}
            if test_data is not None:
                accuracy = self.evaluate(test_data)
                metrics["test_accuracy"] = accuracy
                metrics["test_total"] = len(test_data)

            history.append(metrics)

        return history

    def evaluate(self, test_data: list[tuple[NDArrayFloat, NDArrayFloat]]) -> int:
        """Evaluate network accuracy on test data.

        Args:
            test_data: List of (input, expected_output) tuples

        Returns:
            Number of correct predictions
        """
        test_results = [
            (np.argmax(self.feedforward(x)), np.argmax(y))
            for x, y in test_data
        ]
        return sum(int(pred == actual) for pred, actual in test_results)

    def _update_mini_batch(
        self,
        mini_batch: list[tuple[NDArrayFloat, NDArrayFloat]],
        learning_rate: float,
    ) -> None:
        """Update weights and biases using backpropagation on mini-batch.

        Args:
            mini_batch: List of (input, target) tuples
            learning_rate: Learning rate for gradient descent
        """
        # Initialize gradient accumulators
        nabla_b: list[NDArrayFloat] = [np.zeros(b.shape) for b in self.biases]
        nabla_w: list[NDArrayFloat] = [np.zeros(w.shape) for w in self.weights]

        # Accumulate gradients across mini-batch
        for x, y in mini_batch:
            delta_nabla_b, delta_nabla_w = self._backprop(x, y)
            nabla_b = [nb + dnb for nb, dnb in zip(nabla_b, delta_nabla_b)]
            nabla_w = [nw + dnw for nw, dnw in zip(nabla_w, delta_nabla_w)]

        # Update weights and biases
        eta_over_m = learning_rate / len(mini_batch)
        self.weights = [
            w - eta_over_m * nw for w, nw in zip(self.weights, nabla_w)
        ]
        self.biases = [
            b - eta_over_m * nb for b, nb in zip(self.biases, nabla_b)
        ]

    def _backprop(
        self,
        x: NDArrayFloat,
        y: NDArrayFloat,
    ) -> tuple[list[NDArrayFloat], list[NDArrayFloat]]:
        """Compute gradients using backpropagation.

        Args:
            x: Input vector
            y: Target output vector

        Returns:
            Tuple of (bias_gradients, weight_gradients)
        """
        nabla_b: list[NDArrayFloat] = [np.zeros(b.shape) for b in self.biases]
        nabla_w: list[NDArrayFloat] = [np.zeros(w.shape) for w in self.weights]

        # Forward pass - store activations and z values
        activation = x
        activations: list[NDArrayFloat] = [x]
        zs: list[NDArrayFloat] = []

        for b, w in zip(self.biases, self.weights):
            z = w @ activation + b
            zs.append(z)
            activation = self._activation(z)
            activations.append(activation)

        # Backward pass - compute deltas
        delta = self._cost_derivative(activations[-1], y) * self._activation_derivative(zs[-1])
        nabla_b[-1] = delta
        nabla_w[-1] = delta @ activations[-2].T

        # Backpropagate through layers
        for layer in range(2, self.num_layers):
            z = zs[-layer]
            sp = self._activation_derivative(z)
            delta = (self.weights[-layer + 1].T @ delta) * sp
            nabla_b[-layer] = delta
            nabla_w[-layer] = delta @ activations[-layer - 1].T

        return nabla_b, nabla_w

    def _activation(self, z: NDArrayFloat) -> NDArrayFloat:
        """Apply activation function.

        Args:
            z: Pre-activation values

        Returns:
            Activated values
        """
        match self.activation_name:
            case "sigmoid":
                return 1.0 / (1.0 + np.exp(-z))
            case "relu":
                return np.maximum(0.0, z)

    def _activation_derivative(self, z: NDArrayFloat) -> NDArrayFloat:
        """Compute derivative of activation function.

        Args:
            z: Pre-activation values

        Returns:
            Derivative values
        """
        match self.activation_name:
            case "sigmoid":
                sig = self._activation(z)
                return sig * (1.0 - sig)
            case "relu":
                return (z > 0).astype(np.float64)

    @staticmethod
    def _cost_derivative(
        output_activations: NDArrayFloat,
        y: NDArrayFloat,
    ) -> NDArrayFloat:
        """Compute derivative of quadratic cost function.

        Args:
            output_activations: Network output
            y: Target output

        Returns:
            Cost derivative
        """
        return output_activations - y

    def to_dict(self) -> dict[str, list[list[float]] | list[int] | str]:
        """Export network state to dictionary.

        Returns:
            Dictionary with weights, biases, and configuration
        """
        return {
            "sizes": self.sizes,
            "activation": self.activation_name,
            "weights": [w.tolist() for w in self.weights],
            "biases": [b.tolist() for b in self.biases],
        }

    @classmethod
    def from_dict(cls, data: dict[str, list[list[float]] | list[int] | str]) -> "NeuralNetwork":
        """Load network from dictionary.

        Args:
            data: Dictionary with network configuration and parameters

        Returns:
            Reconstructed neural network

        Raises:
            ValueError: If data format is invalid
        """
        if not isinstance(data.get("sizes"), list):
            raise ValueError("Missing or invalid 'sizes' field")
        if not isinstance(data.get("activation"), str):
            raise ValueError("Missing or invalid 'activation' field")

        sizes = data["sizes"]
        activation = data["activation"]

        if activation not in ("sigmoid", "relu"):
            raise ValueError(f"Invalid activation: {activation}")

        network = cls(sizes, activation)  # type: ignore

        if "weights" in data and "biases" in data:
            network.weights = [np.array(w, dtype=np.float64) for w in data["weights"]]
            network.biases = [np.array(b, dtype=np.float64) for b in data["biases"]]

        return network
