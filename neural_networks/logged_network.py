"""Logged neural network wrapper for learning and debugging.

Wraps NeuralNetwork with comprehensive logging WITHOUT modifying the original class.
Use this when you want to see what's happening inside during training.
"""

import time
from typing import Any
import numpy as np

from neural_networks.core import NeuralNetwork, NDArrayFloat
from neural_networks.training_logger import TrainingLogger


class LoggedNeuralNetwork:
    """Wrapper that logs all training activity without modifying core network.

    Usage:
        # Instead of:
        network = NeuralNetwork([784, 30, 10])

        # Use:
        network = LoggedNeuralNetwork([784, 30, 10])

        # Everything works the same, but now logs to logs/ directory
        network.train(training_data, epochs=30, ...)
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize logged network.

        Args:
            *args: Forwarded to NeuralNetwork
            **kwargs: Forwarded to NeuralNetwork
        """
        self._network = NeuralNetwork(*args, **kwargs)
        self._logger = TrainingLogger()

    def __getattr__(self, name: str) -> Any:
        """Forward all attribute access to underlying network.

        Args:
            name: Attribute name

        Returns:
            Attribute from underlying network
        """
        return getattr(self._network, name)

    def train(
        self,
        training_data: list[tuple[NDArrayFloat, NDArrayFloat]],
        epochs: int,
        mini_batch_size: int,
        learning_rate: float,
        test_data: list[tuple[NDArrayFloat, NDArrayFloat]] | None = None,
    ) -> list[dict[str, int | float]]:
        """Train with comprehensive logging.

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
        training_start = time.time()

        print(f"🔬 Training with logging enabled")
        print(f"📁 Logs will be saved to: {self._logger.log_file}\n")

        for epoch in range(epochs):
            epoch_start = time.time()
            self._logger.log_epoch_start(epoch + 1, epochs)

            # Shuffle and create mini-batches
            np.random.shuffle(training_data)
            mini_batches = [
                training_data[k:k + mini_batch_size]
                for k in range(0, n, mini_batch_size)
            ]

            # Train each mini-batch and log periodically
            for batch_idx, mini_batch in enumerate(mini_batches):
                # Store pre-update weights
                old_weights = [w.copy() for w in self._network.weights]
                old_biases = [b.copy() for b in self._network.biases]

                # Update (original method)
                self._network._update_mini_batch(mini_batch, learning_rate)

                # Compute what changed (gradients applied)
                if batch_idx % 100 == 0:  # Log every 100th batch
                    weight_deltas = [
                        new - old for new, old in zip(self._network.weights, old_weights)
                    ]
                    bias_deltas = [
                        new - old for new, old in zip(self._network.biases, old_biases)
                    ]
                    self._logger.log_mini_batch(
                        epoch + 1,
                        batch_idx,
                        len(mini_batch),
                        bias_deltas,
                        weight_deltas,
                    )

            # Log weight snapshot after epoch
            self._logger.log_weights_snapshot(
                epoch + 1,
                self._network.weights,
                self._network.biases,
            )

            # Evaluate
            epoch_duration = time.time() - epoch_start
            metrics: dict[str, int | float] = {"epoch": epoch + 1}
            test_accuracy = None
            test_total = None

            if test_data is not None:
                test_accuracy = self._network.evaluate(test_data)
                test_total = len(test_data)
                metrics["test_accuracy"] = test_accuracy
                metrics["test_total"] = test_total

                accuracy_pct = (test_accuracy / test_total) * 100
                print(f"Epoch {epoch + 1}/{epochs}: {accuracy_pct:.2f}% accuracy ({test_accuracy}/{test_total})")

            self._logger.log_epoch_end(epoch + 1, test_accuracy, test_total, epoch_duration)
            history.append(metrics)

        # Training complete
        total_duration = time.time() - training_start
        self._logger.log_training_complete(total_duration)

        print(f"\n✅ Training complete!")
        print(f"📊 Logs saved to: {self._logger.log_file}")
        print(f"📈 Summary: {self._logger.get_summary()}")

        return history

    @property
    def logger(self) -> TrainingLogger:
        """Access to logger for custom logging.

        Returns:
            Training logger instance
        """
        return self._logger

    @property
    def network(self) -> NeuralNetwork:
        """Access to underlying network.

        Returns:
            Underlying NeuralNetwork instance
        """
        return self._network
