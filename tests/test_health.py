"""Tests for health check endpoint."""

from fastapi.testclient import TestClient

from neural_networks.core import NeuralNetwork


def test_health_check_without_network(client: TestClient) -> None:
    """Test health check endpoint when network is not loaded.

    Args:
        client: FastAPI test client
    """
    response = client.get("/healthz")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "network_loaded" in data
    assert "database_connected" in data


def test_health_check_with_network(
    client: TestClient, mock_network: NeuralNetwork
) -> None:
    """Test health check endpoint when network is loaded.

    Args:
        client: FastAPI test client
        mock_network: Mock neural network fixture
    """
    response = client.get("/healthz")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["network_loaded"] is True
    assert isinstance(data["database_connected"], bool)


def test_health_check_response_schema(client: TestClient) -> None:
    """Test that health check response matches expected schema.

    Args:
        client: FastAPI test client
    """
    response = client.get("/healthz")

    assert response.status_code == 200
    data = response.json()

    # Check required fields
    assert "status" in data
    assert "network_loaded" in data
    assert "database_connected" in data

    # Check types
    assert isinstance(data["status"], str)
    assert isinstance(data["network_loaded"], bool)
    assert isinstance(data["database_connected"], bool)
