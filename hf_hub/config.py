"""Hugging Face Hub configuration."""

import os
from pathlib import Path


def get_hf_token() -> str | None:
    """Get Hugging Face token from environment.

    Returns:
        HF token or None if not set
    """
    return os.getenv("HUGGINGFACE_TOKEN")


def get_repo_id() -> str:
    """Get HF Hub repository ID from environment.

    Returns:
        Repository ID

    Raises:
        RuntimeError: If HF_MODEL_REPO not set
    """
    repo_id = os.getenv("HF_MODEL_REPO")
    if not repo_id:
        raise RuntimeError(
            "HF_MODEL_REPO environment variable not set. "
            "Example: export HF_MODEL_REPO=username/hippo-models"
        )
    return repo_id


def get_default_model() -> str:
    """Get default model name from environment.

    Returns:
        Default model name

    Raises:
        RuntimeError: If DEFAULT_MODEL not set
    """
    model = os.getenv("DEFAULT_MODEL")
    if not model:
        raise RuntimeError(
            "DEFAULT_MODEL environment variable not set. "
            "Example: export DEFAULT_MODEL=mnist-relu-100"
        )
    return model


def get_cache_dir() -> Path:
    """Get local cache directory for downloaded models.

    Returns:
        Path to cache directory
    """
    cache_dir = os.getenv("HF_CACHE_DIR", ".hf_cache")
    return Path(cache_dir)
