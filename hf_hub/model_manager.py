"""Model manager for Hugging Face Hub integration."""

import json
from pathlib import Path
from typing import Any

import numpy as np
from huggingface_hub import hf_hub_download

from hf_hub.config import get_cache_dir, get_hf_token, get_repo_id
from neural_networks.core import NeuralNetwork


class ModelManager:
    """Manage models from Hugging Face Hub.

    Handles downloading, caching, and loading neural network models
    from HF Hub repository.
    """

    def __init__(
        self,
        repo_id: str | None = None,
        cache_dir: Path | None = None,
        token: str | None = None,
    ) -> None:
        """Initialize model manager.

        Args:
            repo_id: HF Hub repository ID (default: from HF_MODEL_REPO env var)
            cache_dir: Local cache directory (default: from config)
            token: HF token for private repos (default: from HUGGINGFACE_TOKEN env var)
        """
        self.repo_id = repo_id or get_repo_id()
        self.cache_dir = cache_dir or get_cache_dir()
        self.token = token or get_hf_token()

        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def download_model(self, model_name: str) -> tuple[Path, Path]:
        """Download model files from HF Hub.

        Args:
            model_name: Name of the model (without .npz extension)

        Returns:
            Tuple of (model_path, metadata_path)

        Raises:
            Exception: If download fails
        """
        model_filename = f"{model_name}.npz"
        metadata_filename = f"{model_name}.json"

        # Download model file
        model_path = Path(
            hf_hub_download(
                repo_id=self.repo_id,
                filename=model_filename,
                cache_dir=str(self.cache_dir),
                token=self.token,
            )
        )

        # Download metadata file
        metadata_path = Path(
            hf_hub_download(
                repo_id=self.repo_id,
                filename=metadata_filename,
                cache_dir=str(self.cache_dir),
                token=self.token,
            )
        )

        return model_path, metadata_path

    def load_metadata(self, metadata_path: Path) -> dict[str, Any]:
        """Load model metadata from JSON file.

        Args:
            metadata_path: Path to metadata JSON file

        Returns:
            Model metadata dictionary
        """
        with open(metadata_path) as f:
            return json.load(f)

    def load_model(self, model_name: str) -> NeuralNetwork:
        """Load model from HF Hub.

        Downloads model if not cached, then loads into NeuralNetwork instance.

        Args:
            model_name: Name of the model (without .npz extension)

        Returns:
            Loaded NeuralNetwork instance

        Raises:
            Exception: If model cannot be loaded
        """
        # Download model files (uses cache if available)
        model_path, _metadata_path = self.download_model(model_name)

        # Load model data
        data = np.load(model_path)

        # Extract architecture
        sizes = data["sizes"].tolist()
        activation = str(data["activation"])
        num_layers = int(data["num_layers"])

        # Reconstruct weights and biases from individual arrays
        weights = [data[f"weight_{i}"] for i in range(num_layers - 1)]
        biases = [data[f"bias_{i}"] for i in range(num_layers - 1)]

        # Create network with loaded parameters
        network_dict: dict[str, object] = {
            "sizes": sizes,
            "activation": activation,
            "weights": weights,
            "biases": biases,
        }

        return NeuralNetwork.from_dict(network_dict)

    def get_model_info(self, model_name: str) -> dict[str, Any]:
        """Get model metadata without loading the full model.

        Args:
            model_name: Name of the model

        Returns:
            Model metadata dictionary
        """
        _, metadata_path = self.download_model(model_name)
        return self.load_metadata(metadata_path)

    def list_cached_models(self) -> list[str]:
        """List models available in local cache.

        Returns:
            List of cached model names (without .npz extension)
        """
        if not self.cache_dir.exists():
            return []

        cached_models = []
        for path in self.cache_dir.rglob("*.npz"):
            model_name = path.stem
            cached_models.append(model_name)

        return sorted(set(cached_models))

    def clear_cache(self) -> None:
        """Clear local model cache.

        Removes all downloaded model files.
        """
        if self.cache_dir.exists():
            import shutil

            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
