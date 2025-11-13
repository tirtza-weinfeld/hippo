"""Example: Train with detailed logging for learning purposes.

This demonstrates how to use LoggedNeuralNetwork to capture everything
that happens during training, then analyze it in a Jupyter notebook.
"""

from neural_networks import MNISTLoader
from neural_networks.logged_network import LoggedNeuralNetwork


def main() -> None:
    """Train a neural network with full logging enabled."""
    print("🔬 Neural Network Training with Logging\n")
    print("=" * 60)

    # Load MNIST data
    print("📦 Loading MNIST dataset...")
    training_data, validation_data, test_data = MNISTLoader.load_data()
    print(f"✅ Loaded {len(training_data)} training samples\n")

    # Create logged network (wrapper around NeuralNetwork)
    print("🧠 Creating neural network...")
    network = LoggedNeuralNetwork([784, 30, 10], activation="sigmoid")
    print(f"✅ Network created: {network.sizes}")
    print(f"   Activation: {network.activation_name}\n")

    # Train with logging
    print("🚀 Starting training...")
    print("-" * 60)

    network.train(
        training_data=training_data[:5000],  # Use subset for faster demo
        epochs=5,
        mini_batch_size=10,
        learning_rate=3.0,
        test_data=test_data,
    )

    print("-" * 60)
    print("\n✅ Training complete!")
    print("\n📊 Next steps:")
    print("   1. Open notebooks/analyze_training.ipynb in Jupyter")
    print("   2. Run all cells to visualize what happened")
    print("   3. See accuracy curves, weight evolution, gradient magnitudes")
    print("\n💡 What you'll learn:")
    print("   • How accuracy improves over epochs")
    print("   • How weights change during training")
    print("   • How gradient sizes evolve")
    print("   • How long each epoch takes")


if __name__ == "__main__":
    main()
