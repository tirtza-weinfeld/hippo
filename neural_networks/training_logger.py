"""Training logger for detailed neural network insights.

Captures everything happening during training for learning purposes:
- Weight/bias changes
- Gradient magnitudes
- Activation patterns
- Loss per mini-batch
- Layer-wise statistics
"""

import json
from pathlib import Path
from typing import Any
from datetime import datetime

import numpy as np
import numpy.typing as npt


NDArrayFloat = npt.NDArray[np.floating]


class TrainingLogger:
    """Captures detailed training metrics for analysis and visualization."""

    def __init__(self, log_dir: Path = Path("logs")) -> None:
        """Initialize training logger.

        Args:
            log_dir: Directory to save log files
        """
        self.log_dir = log_dir
        self.log_dir.mkdir(exist_ok=True)

        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"training_{self.session_id}.jsonl"

        self.epoch_metrics: list[dict[str, Any]] = []
        self.mini_batch_metrics: list[dict[str, Any]] = []
        self.weight_history: list[dict[str, Any]] = []

    def log_epoch_start(self, epoch: int, total_epochs: int) -> None:
        """Log start of epoch.

        Args:
            epoch: Current epoch number
            total_epochs: Total number of epochs
        """
        entry = {
            "type": "epoch_start",
            "timestamp": datetime.now().isoformat(),
            "epoch": epoch,
            "total_epochs": total_epochs,
        }
        self._write_log(entry)

    def log_mini_batch(
        self,
        epoch: int,
        batch_idx: int,
        batch_size: int,
        gradients_b: list[NDArrayFloat],
        gradients_w: list[NDArrayFloat],
    ) -> None:
        """Log mini-batch training step.

        Args:
            epoch: Current epoch
            batch_idx: Mini-batch index
            batch_size: Size of mini-batch
            gradients_b: Bias gradients
            gradients_w: Weight gradients
        """
        # Compute gradient statistics
        grad_stats = {
            "bias_mean": [float(np.mean(np.abs(g))) for g in gradients_b],
            "bias_max": [float(np.max(np.abs(g))) for g in gradients_b],
            "weight_mean": [float(np.mean(np.abs(g))) for g in gradients_w],
            "weight_max": [float(np.max(np.abs(g))) for g in gradients_w],
        }

        entry = {
            "type": "mini_batch",
            "timestamp": datetime.now().isoformat(),
            "epoch": epoch,
            "batch_idx": batch_idx,
            "batch_size": batch_size,
            "gradient_stats": grad_stats,
        }

        self.mini_batch_metrics.append(entry)
        self._write_log(entry)

    def log_weights_snapshot(
        self,
        epoch: int,
        weights: list[NDArrayFloat],
        biases: list[NDArrayFloat],
    ) -> None:
        """Log snapshot of weights and biases.

        Args:
            epoch: Current epoch
            weights: Network weights
            biases: Network biases
        """
        entry = {
            "type": "weight_snapshot",
            "timestamp": datetime.now().isoformat(),
            "epoch": epoch,
            "layers": [
                {
                    "layer": idx,
                    "weight_mean": float(np.mean(w)),
                    "weight_std": float(np.std(w)),
                    "weight_min": float(np.min(w)),
                    "weight_max": float(np.max(w)),
                    "bias_mean": float(np.mean(b)),
                    "bias_std": float(np.std(b)),
                }
                for idx, (w, b) in enumerate(zip(weights, biases))
            ],
        }

        self.weight_history.append(entry)
        self._write_log(entry)

    def log_epoch_end(
        self,
        epoch: int,
        test_accuracy: int | None,
        test_total: int | None,
        epoch_duration: float,
    ) -> None:
        """Log end of epoch with metrics.

        Args:
            epoch: Current epoch
            test_accuracy: Number of correct predictions
            test_total: Total test samples
            epoch_duration: Time taken for epoch (seconds)
        """
        accuracy_percent = None
        if test_accuracy is not None and test_total is not None:
            accuracy_percent = (test_accuracy / test_total) * 100

        entry = {
            "type": "epoch_end",
            "timestamp": datetime.now().isoformat(),
            "epoch": epoch,
            "test_accuracy": test_accuracy,
            "test_total": test_total,
            "accuracy_percent": accuracy_percent,
            "duration_seconds": epoch_duration,
        }

        self.epoch_metrics.append(entry)
        self._write_log(entry)

    def log_activation_pattern(
        self,
        sample_idx: int,
        activations: list[NDArrayFloat],
        label: int,
        prediction: int,
    ) -> None:
        """Log activation pattern for a sample.

        Args:
            sample_idx: Sample index
            activations: Activations for all layers
            label: True label
            prediction: Predicted label
        """
        entry = {
            "type": "activation_pattern",
            "timestamp": datetime.now().isoformat(),
            "sample_idx": sample_idx,
            "label": label,
            "prediction": prediction,
            "correct": label == prediction,
            "layer_activations": [
                {
                    "layer": idx,
                    "mean_activation": float(np.mean(act)),
                    "max_activation": float(np.max(act)),
                    "active_neurons": int(np.sum(act > 0.5)),
                    "total_neurons": act.size,
                }
                for idx, act in enumerate(activations)
            ],
        }
        self._write_log(entry)

    def log_training_complete(self, total_duration: float) -> None:
        """Log training completion.

        Args:
            total_duration: Total training time (seconds)
        """
        entry = {
            "type": "training_complete",
            "timestamp": datetime.now().isoformat(),
            "total_duration_seconds": total_duration,
            "session_id": self.session_id,
        }
        self._write_log(entry)

    def _write_log(self, entry: dict[str, Any]) -> None:
        """Write log entry to file.

        Args:
            entry: Log entry dictionary
        """
        with self.log_file.open("a") as f:
            f.write(json.dumps(entry) + "\n")

    def get_summary(self) -> dict[str, Any]:
        """Get training summary statistics.

        Returns:
            Summary dictionary with key metrics
        """
        if not self.epoch_metrics:
            return {"status": "no_data"}

        accuracies = [
            m["accuracy_percent"]
            for m in self.epoch_metrics
            if m.get("accuracy_percent") is not None
        ]

        return {
            "session_id": self.session_id,
            "total_epochs": len(self.epoch_metrics),
            "final_accuracy": accuracies[-1] if accuracies else None,
            "best_accuracy": max(accuracies) if accuracies else None,
            "accuracy_improvement": accuracies[-1] - accuracies[0] if len(accuracies) > 1 else None,
            "log_file": str(self.log_file),
        }


def load_training_logs(log_file: Path) -> list[dict[str, Any]]:
    """Load training logs from file.

    Args:
        log_file: Path to log file

    Returns:
        List of log entries
    """
    logs: list[dict[str, Any]] = []
    with log_file.open() as f:
        for line in f:
            logs.append(json.loads(line))
    return logs
