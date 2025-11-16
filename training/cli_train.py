"""CLI wrapper for training neural networks.

Handles argument parsing, user output, and calls pure training logic.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

from training.train import train_network, save_model

# Load environment variables
load_dotenv()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Train feedforward neural network on MNIST"
    )
    parser.add_argument(
        "--sizes",
        type=int,
        nargs="+",
        required=True,
        help="Layer sizes (e.g., 784 100 10)",
    )
    parser.add_argument(
        "--activation",
        type=str,
        choices=["sigmoid", "relu"],
        default="sigmoid",
        help="Activation function",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=30,
        help="Number of training epochs",
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=3.0,
        help="Learning rate",
    )
    parser.add_argument(
        "--mini-batch-size",
        type=int,
        default=10,
        help="Mini-batch size",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (default: auto-generated in models/)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility",
    )
    return parser.parse_args()


def main() -> None:
    """Main CLI entry point."""
    args = parse_args()

    # Print configuration
    if args.seed is not None:
        print(f"Random seed: {args.seed}")

    print("Loading MNIST dataset...")
    print(f"\nCreating network: {args.sizes}")
    print(f"Activation: {args.activation}")
    print(f"\nTraining for {args.epochs} epochs...")
    print(f"Learning rate: {args.learning_rate}")
    print(f"Mini-batch size: {args.mini_batch_size}")
    print("-" * 50)

    # Train network (pure logic, no side effects)
    network, final_accuracy = train_network(
        sizes=args.sizes,
        activation=args.activation,  # type: ignore[arg-type]
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        mini_batch_size=args.mini_batch_size,
        seed=args.seed,
    )

    # Print results
    print("-" * 50)
    print("\n✓ Training complete!")
    print(f"Final accuracy: {final_accuracy:.2f}%")

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hidden_sizes = "-".join(str(s) for s in args.sizes[1:-1])
        filename = f"mnist-{args.activation}-{hidden_sizes}-{timestamp}.npz"
        output_path = Path("models") / filename

    # Save model with metadata
    training_config = {
        "sizes": args.sizes,
        "activation": args.activation,
        "epochs": args.epochs,
        "learning_rate": args.learning_rate,
        "mini_batch_size": args.mini_batch_size,
        "seed": args.seed,
    }

    save_model(
        network=network,
        filepath=output_path,
        metadata={
            "training_config": training_config,
            "final_accuracy": final_accuracy,
        },
    )

    # Print file info
    print(f"✓ Model saved to: {output_path}")
    print(f"  Size: {output_path.stat().st_size / 1024:.1f} KB")

    # Prompt for upload to HuggingFace Hub
    print("\n" + "=" * 50)
    upload_choice = input("Upload model to HuggingFace Hub? (y/n): ").strip().lower()

    if upload_choice == "y":
        import os

        from training.upload import upload_model_to_hub

        # Get repo ID and token
        repo_id = os.getenv("HF_MODEL_REPO")
        token = os.getenv("HUGGINGFACE_TOKEN")

        if not repo_id:
            print("\n✗ Error: HF_MODEL_REPO environment variable not set")
            print("Add to .env: HF_MODEL_REPO=username/hippo-models")
            print("\nManual upload:")
            print(f"  make upload MODEL={output_path} ACC={final_accuracy:.2f}")
            return

        if not token:
            print("\n✗ Error: HUGGINGFACE_TOKEN environment variable not set")
            print("Run: huggingface-cli login")
            print("Or add HUGGINGFACE_TOKEN to .env")
            print("\nManual upload:")
            print(f"  make upload MODEL={output_path} ACC={final_accuracy:.2f}")
            return

        # Get model name from filename
        model_name = output_path.stem

        # Optional description
        description = input(
            "Model description (optional, press Enter to skip): "
        ).strip()
        if not description:
            hidden_sizes = "-".join(str(s) for s in args.sizes[1:-1])
            description = f"{hidden_sizes} hidden neurons, {args.activation} activation"

        print(f"\nUploading {model_name} to {repo_id}...")

        try:
            uploaded = upload_model_to_hub(
                model_path=output_path,
                repo_id=repo_id,
                model_name=model_name,
                token=token,
                description=description,
                accuracy=final_accuracy,
            )

            print(f"✓ Uploaded {model_name}.npz")
            print(f"✓ Uploaded {model_name}.json")
            if "readme" in uploaded:
                print("✓ Uploaded README.md")

            print("\n✓ Upload complete!")
            print(f"View your model: https://huggingface.co/{repo_id}")

            # Prompt to update .env
            print("\n" + "=" * 50)
            update_env = (
                input(f"Update DEFAULT_MODEL in .env to {model_name}? (y/n): ")
                .strip()
                .lower()
            )

            if update_env == "y":
                env_path = Path(".env")
                if env_path.exists():
                    env_content = env_path.read_text()

                    # Update DEFAULT_MODEL line
                    import re

                    new_content = re.sub(
                        r"^DEFAULT_MODEL=.*$",
                        f"DEFAULT_MODEL={model_name}",
                        env_content,
                        flags=re.MULTILINE,
                    )

                    env_path.write_text(new_content)
                    print(f"✓ Updated .env: DEFAULT_MODEL={model_name}")
                else:
                    print("✗ .env file not found")

            # Prompt to start API
            print("\n" + "=" * 50)
            start_api = input("Start API locally to test? (y/n): ").strip().lower()

            if start_api == "y":
                print("\n✓ Starting API server...")
                print("API will be available at: http://localhost:8000")
                print("Interactive docs: http://localhost:8000/docs")
                print("\nPress Ctrl+C to stop the server\n")

                import subprocess

                try:
                    subprocess.run(["make", "start"])
                except KeyboardInterrupt:
                    print("\n\n✓ API server stopped")
            else:
                print("\nTo start API later: make start")

            # Info about Railway deployment
            print("\n" + "=" * 50)
            print("When ready to deploy to Railway:")
            print("1. Set environment variables in Railway dashboard")
            print(f"   DEFAULT_MODEL={model_name}")
            print("2. Deploy: railway up")

        except Exception as e:
            print(f"\n✗ Upload failed: {e}")
            print("\nManual upload:")
            print(f"  make upload MODEL={output_path} ACC={final_accuracy:.2f}")

    else:
        print("\nSkipping upload. To upload later:")
        print(f"  make upload MODEL={output_path} ACC={final_accuracy:.2f}")
        print("\nNext steps:")
        print("1. Upload to HF Hub (when ready)")
        print("2. Update .env with model name")
        print("3. Restart API: make start")


if __name__ == "__main__":
    main()
