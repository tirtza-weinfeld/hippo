"""Quick test script for the deployed API."""

import requests

API_URL = "https://hippo.up.railway.app"


def test_health() -> None:
    """Test health endpoint."""
    response = requests.get(f"{API_URL}/healthz", timeout=10)
    print(f"Health Check: {response.status_code}")
    print(response.json())
    print()


def test_prediction() -> None:
    """Test prediction with sample data (all zeros)."""
    # Create 784 zeros (28x28 image)
    pixels = [0.0] * 784

    # Add some pattern in the middle to make it interesting
    # Create a simple vertical line
    for i in range(10, 20):
        pixels[14 * 28 + i] = 1.0  # Row 14, columns 10-19

    response = requests.post(
        f"{API_URL}/predict",
        json={"pixels": pixels},
        timeout=10,
    )

    print(f"Prediction: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"  Predicted digit: {result['predicted_digit']}")
        print(f"  Confidence: {result['confidence']:.4f}")
        print("  Top 3 probabilities:")
        probs = result["probabilities"]
        sorted_probs = sorted(enumerate(probs), key=lambda x: x[1], reverse=True)
        for digit, prob in sorted_probs[:3]:
            print(f"    Digit {digit}: {prob:.4f}")
    else:
        print(response.json())
    print()


def test_activations() -> None:
    """Test activations endpoint."""
    pixels = [0.0] * 784

    response = requests.post(
        f"{API_URL}/activations",
        json={"pixels": pixels},
        timeout=10,
    )

    print(f"Activations: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"  Layer sizes: {result['layer_sizes']}")
        print(f"  Number of layers: {len(result['activations'])}")
        for i, layer in enumerate(result["activations"]):
            print(f"    Layer {i}: {len(layer)} neurons")
    else:
        print(response.json())


if __name__ == "__main__":
    print("Testing Railway Deployment API")
    print("=" * 50)
    print()

    test_health()
    test_prediction()
    test_activations()

    print("✓ All tests complete!")
