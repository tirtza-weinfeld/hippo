"""Pytest configuration and fixtures for API tests."""

from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from api.main import app
from api.state import state
from db import Base, get_db
from neural_networks.core import NeuralNetwork

# ============================================================================
# Database Fixtures
# ============================================================================


@pytest.fixture
def test_db() -> Generator[Session]:
    """Create a fresh in-memory SQLite database for each test.

    Yields:
        Database session for testing
    """
    # Create in-memory SQLite database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db: Session) -> Generator[TestClient]:
    """Create a test client with overridden database dependency.

    Args:
        test_db: Test database session

    Yields:
        FastAPI test client
    """

    def override_get_db() -> Generator[Session]:
        """Override database dependency."""
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ============================================================================
# Neural Network Fixtures
# ============================================================================


@pytest.fixture
def mock_network() -> Generator[NeuralNetwork]:
    """Create a small mock neural network for testing.

    Yields:
        Mock neural network with small architecture
    """
    # Create a small network for fast tests: 784 -> 10 (no hidden layers)
    network = NeuralNetwork([784, 10], activation="sigmoid")

    # Store original state network
    original_network = state.network

    # Set mock network in state
    state.network = network

    yield network

    # Restore original network
    state.network = original_network


@pytest.fixture
def sample_pixels() -> list[float]:
    """Create sample pixel data for testing (784-dimensional).

    Returns:
        List of 784 float values representing a 28x28 image
    """
    # Create a simple vertical line pattern
    pixels = [0.0] * 784
    for i in range(10, 20):
        pixels[14 * 28 + i] = 1.0  # Row 14, columns 10-19
    return pixels


@pytest.fixture
def zero_pixels() -> list[float]:
    """Create all-zero pixel data for testing.

    Returns:
        List of 784 zeros
    """
    return [0.0] * 784


# ============================================================================
# Vocabulary Data Fixtures
# ============================================================================


@pytest.fixture
def sample_word_data() -> dict[str, Any]:
    """Sample word data for testing.

    Returns:
        Dictionary with word data
    """
    return {
        "word_text": "ephemeral",
        "language_code": "en",
    }


@pytest.fixture
def sample_definition_data() -> dict[str, Any]:
    """Sample definition data for testing.

    Returns:
        Dictionary with definition data
    """
    return {
        "word_id": 1,
        "definition_text": "lasting for a very short time",
        "part_of_speech": "adjective",
        "order": 1,
    }


@pytest.fixture
def sample_example_data() -> dict[str, Any]:
    """Sample example data for testing.

    Returns:
        Dictionary with example data
    """
    return {
        "definition_id": 1,
        "example_text": "fashions are ephemeral: new ones regularly drive out the old",
    }


@pytest.fixture
def sample_tag_data() -> dict[str, Any]:
    """Sample tag data for testing.

    Returns:
        Dictionary with tag data
    """
    return {"name": "vocabulary", "description": "Words for vocabulary building"}
