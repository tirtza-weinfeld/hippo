"""CLI wrapper for uploading models to Hugging Face Hub.

Handles argument parsing, user output, and calls pure upload logic.
"""

import argparse
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

from training.upload import upload_model_to_hub

# Load environment variables
load_dotenv()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Upload trained model to Hugging Face Hub"
    )
    parser.add_argument(
        "--model-path",
        type=str,
        required=True,
        help="Path to .npz model file",
    )
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="Model name (default: filename without extension)",
    )
    parser.add_argument(
        "--description",
        type=str,
        default="",
        help="Model description",
    )
    parser.add_argument(
        "--accuracy",
        type=float,
        required=True,
        help="Test accuracy percentage (e.g., 95.4)",
    )
    parser.add_argument(
        "--repo-id",
        type=str,
        default=None,
        help="HF Hub repo ID (default: from HF_MODEL_REPO env var)",
    )
    return parser.parse_args()


def main() -> None:
    """Main CLI entry point."""
    args = parse_args()

    # Validate model path
    model_path = Path(args.model_path)
    if not model_path.exists():
        print(f"Error: Model file not found: {model_path}")
        return

    # Determine model name
    model_name = args.name or model_path.stem

    # Get repo ID
    repo_id = args.repo_id or os.getenv("HF_MODEL_REPO")
    if not repo_id:
        print("Error: --repo-id not provided and HF_MODEL_REPO env var not set")
        print("Example: export HF_MODEL_REPO=username/hippo-models")
        return

    # Get HF token
    token = os.getenv("HUGGINGFACE_TOKEN")
    if not token:
        print("Error: HUGGINGFACE_TOKEN env var not set")
        print("Run: huggingface-cli login")
        print("Or add HUGGINGFACE_TOKEN to .env")
        return

    # Print upload info
    print(f"Uploading {model_name} to {repo_id}...")
    print(f"\n1. Model file: {model_path}")
    print(f"2. Accuracy: {args.accuracy:.2f}%")
    print(f"3. Repository: {repo_id}")

    # Upload to HF Hub (pure logic)
    try:
        print("\n4. Uploading files...")
        uploaded = upload_model_to_hub(
            model_path=model_path,
            repo_id=repo_id,
            model_name=model_name,
            token=token,
            description=args.description,
            accuracy=args.accuracy,
        )

        # Print success
        print(f"   ✓ Uploaded {model_name}.npz")
        print(f"   ✓ Uploaded {model_name}.json")
        if "readme" in uploaded:
            print("   ✓ Uploaded README.md")

        print("\n✓ Upload complete!")
        print(f"\nView your model: https://huggingface.co/{repo_id}")
        print("\nNext steps:")
        print("1. Update .env:")
        print(f"   DEFAULT_MODEL={model_name}")
        print("2. Restart API:")
        print("   make start")

    except Exception as e:
        print(f"\n✗ Upload failed: {e}")
        return


if __name__ == "__main__":
    main()
