"""Tests for inference endpoints (/predict, /activations)."""

from fastapi.testclient import TestClient

from neural_networks.core import NeuralNetwork

# ============================================================================
# /predict Endpoint Tests
# ============================================================================


def test_predict_without_network(
    client: TestClient, sample_pixels: list[float]
) -> None:
    """Test prediction endpoint when network is not loaded.

    Args:
        client: FastAPI test client
        sample_pixels: Sample pixel data
    """
    # Import here to avoid circular imports
    from api.state import state

    # Save current network and clear it
    original_network = state.network
    state.network = None

    try:
        response = client.post("/v1/predict", json={"pixels": sample_pixels})

        assert response.status_code == 503
        data = response.json()
        assert "detail" in data
        assert "No model loaded" in data["detail"]
    finally:
        # Restore network
        state.network = original_network


def test_predict_with_network(
    client: TestClient, mock_network: NeuralNetwork, sample_pixels: list[float]
) -> None:
    """Test prediction endpoint with loaded network.

    Args:
        client: FastAPI test client
        mock_network: Mock neural network
        sample_pixels: Sample pixel data
    """
    response = client.post("/v1/predict", json={"pixels": sample_pixels})

    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert "predicted_digit" in data
    assert "confidence" in data
    assert "probabilities" in data

    # Check types and values
    assert isinstance(data["predicted_digit"], int)
    assert 0 <= data["predicted_digit"] <= 9
    assert isinstance(data["confidence"], float)
    assert isinstance(data["probabilities"], list)
    assert len(data["probabilities"]) == 10

    # All probabilities should be positive (sigmoid outputs)
    assert all(p >= 0 for p in data["probabilities"])


def test_predict_with_zeros(
    client: TestClient, mock_network: NeuralNetwork, zero_pixels: list[float]
) -> None:
    """Test prediction with all-zero input.

    Args:
        client: FastAPI test client
        mock_network: Mock neural network
        zero_pixels: All-zero pixel data
    """
    response = client.post("/v1/predict", json={"pixels": zero_pixels})

    assert response.status_code == 200
    data = response.json()
    assert "predicted_digit" in data
    assert "confidence" in data
    assert "probabilities" in data


def test_predict_invalid_input_size(
    client: TestClient, mock_network: NeuralNetwork
) -> None:
    """Test prediction with wrong input size.

    Args:
        client: FastAPI test client
        mock_network: Mock neural network
    """
    # Too few pixels
    response = client.post("/v1/predict", json={"pixels": [0.0] * 100})
    assert response.status_code in [422, 500]  # Validation or runtime error


def test_predict_invalid_pixel_values(
    client: TestClient, mock_network: NeuralNetwork
) -> None:
    """Test prediction with invalid pixel values (non-numeric).

    Args:
        client: FastAPI test client
        mock_network: Mock neural network
    """
    response = client.post("/v1/predict", json={"pixels": ["invalid"] * 784})
    assert response.status_code == 422  # Validation error


def test_predict_missing_field(client: TestClient, mock_network: NeuralNetwork) -> None:
    """Test prediction with missing required field.

    Args:
        client: FastAPI test client
        mock_network: Mock neural network
    """
    response = client.post("/v1/predict", json={})
    assert response.status_code == 422  # Validation error


# ============================================================================
# /activations Endpoint Tests
# ============================================================================


def test_activations_without_network(
    client: TestClient, sample_pixels: list[float]
) -> None:
    """Test activations endpoint when network is not loaded.

    Args:
        client: FastAPI test client
        sample_pixels: Sample pixel data
    """
    # Import here to avoid circular imports
    from api.state import state

    # Save current network and clear it
    original_network = state.network
    state.network = None

    try:
        response = client.post("/v1/activations", json={"pixels": sample_pixels})

        assert response.status_code == 503
        data = response.json()
        assert "detail" in data
        assert "No model loaded" in data["detail"]
    finally:
        # Restore network
        state.network = original_network


def test_activations_with_network(
    client: TestClient, mock_network: NeuralNetwork, sample_pixels: list[float]
) -> None:
    """Test activations endpoint with loaded network.

    Args:
        client: FastAPI test client
        mock_network: Mock neural network
        sample_pixels: Sample pixel data
    """
    response = client.post("/v1/activations", json={"pixels": sample_pixels})

    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert "activations" in data
    assert "layer_sizes" in data

    # Check types
    assert isinstance(data["activations"], list)
    assert isinstance(data["layer_sizes"], list)

    # Check layer sizes match network architecture
    assert data["layer_sizes"] == mock_network.sizes

    # Check activations for each layer
    for i, (activation, size) in enumerate(
        zip(data["activations"], data["layer_sizes"], strict=False)
    ):
        assert isinstance(activation, list)
        assert len(activation) == size, f"Layer {i} activation size mismatch"
        # All activations should be floats
        assert all(isinstance(val, float) for val in activation)


def test_activations_with_zeros(
    client: TestClient, mock_network: NeuralNetwork, zero_pixels: list[float]
) -> None:
    """Test activations with all-zero input.

    Args:
        client: FastAPI test client
        mock_network: Mock neural network
        zero_pixels: All-zero pixel data
    """
    response = client.post("/v1/activations", json={"pixels": zero_pixels})

    assert response.status_code == 200
    data = response.json()
    assert "activations" in data
    assert len(data["activations"]) == len(mock_network.sizes)


def test_activations_invalid_input_size(
    client: TestClient, mock_network: NeuralNetwork
) -> None:
    """Test activations with wrong input size.

    Args:
        client: FastAPI test client
        mock_network: Mock neural network
    """
    response = client.post("/v1/activations", json={"pixels": [0.0] * 100})
    assert response.status_code in [422, 500]  # Validation or runtime error


def test_activations_missing_field(
    client: TestClient, mock_network: NeuralNetwork
) -> None:
    """Test activations with missing required field.

    Args:
        client: FastAPI test client
        mock_network: Mock neural network
    """
    response = client.post("/v1/activations", json={})
    assert response.status_code == 422  # Validation error
