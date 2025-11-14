"""Hugging Face Hub integration for model management.

This module provides functionality to download, cache, and load
neural network models from Hugging Face Hub.

Example:
    from hf_hub import ModelManager

    manager = ModelManager()
    network = manager.load_model("mnist-relu-100")
"""

from hf_hub.config import (
    get_cache_dir,
    get_default_model,
    get_hf_token,
    get_repo_id,
)
from hf_hub.model_manager import ModelManager

__all__ = [
    "ModelManager",
    "get_cache_dir",
    "get_default_model",
    "get_hf_token",
    "get_repo_id",
]
