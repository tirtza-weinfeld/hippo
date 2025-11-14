"""Pure upload logic for Hugging Face Hub.

Clean, importable functions without CLI dependencies.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from huggingface_hub import HfApi, create_repo


def load_model_metadata(model_path: Path) -> dict[str, object]:
    """Load model and extract metadata from .npz and .json files.

    Args:
        model_path: Path to .npz model file

    Returns:
        Dictionary with model metadata
    """
    # Load architecture from .npz file
    data = np.load(model_path)

    metadata: dict[str, object] = {
        "architecture": {
            "sizes": data["sizes"].tolist(),
            "activation": str(data["activation"]),
        }
    }

    # Load training metadata from separate .json file if available
    json_path = model_path.with_suffix(".json")
    if json_path.exists():
        with open(json_path) as f:
            json_data = json.load(f)

            # Extract training config
            if "training_config" in json_data:
                config = json_data["training_config"]
                metadata["training"] = {
                    "epochs": config.get("epochs"),
                    "learning_rate": config.get("learning_rate"),
                    "mini_batch_size": config.get("mini_batch_size"),
                    "seed": config.get("seed"),
                }

            # Add final accuracy if available
            if "final_accuracy" in json_data:
                metadata["final_accuracy"] = json_data["final_accuracy"]

    return metadata


def create_model_card(
    model_name: str,
    description: str,
    metadata: dict[str, object],
    accuracy: float,
) -> str:
    """Generate model card README content.

    Args:
        model_name: Name of the model
        description: Model description
        metadata: Model metadata dictionary
        accuracy: Test accuracy percentage

    Returns:
        Model card markdown content
    """
    arch = metadata["architecture"]
    training = metadata.get("training", {})

    sizes_str = " → ".join(str(s) for s in arch["sizes"])

    card = f"""# {model_name}

{description}

## Model Details

- **Architecture**: Feedforward Neural Network
- **Layer sizes**: {sizes_str}
- **Activation**: {arch["activation"]}
- **Test Accuracy**: {accuracy:.2f}%

## Training Details

"""

    if training:
        card += f"""- **Epochs**: {training.get('epochs', 'N/A')}
- **Learning Rate**: {training.get('learning_rate', 'N/A')}
- **Mini-batch Size**: {training.get('mini_batch_size', 'N/A')}
"""

    card += f"""
## Dataset

Trained on MNIST handwritten digits dataset (60,000 training images, 10,000 test images).

## Usage

### Load in API

```bash
# .env
DEFAULT_MODEL={model_name}
```

### Load in Python

```python
from hf_hub import ModelManager

manager = ModelManager()
network = manager.load_model("{model_name}")
```

## Created

{datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}
"""

    return card


def upload_model_to_hub(
    model_path: Path,
    repo_id: str,
    model_name: str,
    token: str,
    description: str = "",
    accuracy: float | None = None,
) -> dict[str, str]:
    """Upload model to HuggingFace Hub.

    Args:
        model_path: Path to .npz model file
        repo_id: HF Hub repository ID (e.g., 'username/repo')
        model_name: Name for the model (without .npz)
        token: HuggingFace token
        description: Model description
        accuracy: Test accuracy percentage

    Returns:
        Dictionary with uploaded file URLs

    Raises:
        FileNotFoundError: If model file doesn't exist
        Exception: If upload fails
    """
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    # Load model metadata
    metadata = load_model_metadata(model_path)

    # Create full metadata JSON
    full_metadata = {
        "name": model_name,
        "description": description,
        **metadata,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    if accuracy is not None:
        full_metadata["performance"] = {
            "test_accuracy": accuracy,
            "test_samples": 10000,
        }

    temp_dir = model_path.parent
    upload_json_path = temp_dir / f"{model_name}_hf_upload.json"
    card_path = temp_dir / f"{model_name}_README.md"

    # Write metadata for upload
    with open(upload_json_path, "w") as f:
        json.dump(full_metadata, f, indent=2)

    # Write model card
    if accuracy is not None:
        model_card = create_model_card(
            model_name=model_name,
            description=description,
            metadata=metadata,
            accuracy=accuracy,
        )
        with open(card_path, "w") as f:
            f.write(model_card)

    # Initialize HF API
    api = HfApi(token=token)

    # Create repo if doesn't exist
    create_repo(repo_id, repo_type="model", exist_ok=True, token=token)

    # Upload files
    uploaded = {}

    # Upload model file
    api.upload_file(
        path_or_fileobj=str(model_path),
        path_in_repo=f"{model_name}.npz",
        repo_id=repo_id,
        token=token,
    )
    uploaded["model"] = f"{repo_id}/{model_name}.npz"

    # Upload metadata
    api.upload_file(
        path_or_fileobj=str(upload_json_path),
        path_in_repo=f"{model_name}.json",
        repo_id=repo_id,
        token=token,
    )
    uploaded["metadata"] = f"{repo_id}/{model_name}.json"

    # Upload model card as README (optional)
    if accuracy is not None:
        try:
            api.upload_file(
                path_or_fileobj=str(card_path),
                path_in_repo="README.md",
                repo_id=repo_id,
                token=token,
            )
            uploaded["readme"] = f"{repo_id}/README.md"
        except Exception:
            # Skip if README already exists
            pass

    # Clean up temporary files
    upload_json_path.unlink(missing_ok=True)
    card_path.unlink(missing_ok=True)

    return uploaded
