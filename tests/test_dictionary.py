"""Tests for dictionary endpoints."""

from typing import Any

from fastapi.testclient import TestClient

# ============================================================================
# Word Endpoints Tests
# ============================================================================


def test_create_word(client: TestClient, sample_word_data: dict[str, Any]) -> None:
    """Test creating a new word.

    Args:
        client: FastAPI test client
        sample_word_data: Sample word data fixture
    """
    response = client.post("/v1/dictionary/words", json=sample_word_data)

    assert response.status_code == 201
    data = response.json()

    assert data["word_text"] == sample_word_data["word_text"]
    assert data["language_code"] == sample_word_data["language_code"]
    assert "id" in data
    assert "created_at" in data


def test_create_duplicate_word(
    client: TestClient, sample_word_data: dict[str, Any]
) -> None:
    """Test creating a duplicate word (should fail).

    Args:
        client: FastAPI test client
        sample_word_data: Sample word data fixture
    """
    # Create first word
    response1 = client.post("/v1/dictionary/words", json=sample_word_data)
    assert response1.status_code == 201

    # Try to create duplicate
    response2 = client.post("/v1/dictionary/words", json=sample_word_data)
    assert response2.status_code == 400
    assert "already exists" in response2.json()["detail"]


def test_list_words_empty(client: TestClient) -> None:
    """Test listing words when database is empty.

    Args:
        client: FastAPI test client
    """
    response = client.get("/v1/dictionary/words")

    assert response.status_code == 200
    data = response.json()

    assert "data" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert len(data["data"]) == 0
    assert data["total"] == 0


def test_list_words_with_data(
    client: TestClient, sample_word_data: dict[str, Any]
) -> None:
    """Test listing words with data.

    Args:
        client: FastAPI test client
        sample_word_data: Sample word data fixture
    """
    # Create a word
    client.post("/v1/dictionary/words", json=sample_word_data)

    # List words
    response = client.get("/v1/dictionary/words")

    assert response.status_code == 200
    data = response.json()

    assert len(data["data"]) == 1
    assert data["total"] == 1
    assert data["data"][0]["word_text"] == sample_word_data["word_text"]


def test_get_word_by_id(client: TestClient, sample_word_data: dict[str, Any]) -> None:
    """Test getting a specific word by ID.

    Args:
        client: FastAPI test client
        sample_word_data: Sample word data fixture
    """
    # Create a word
    create_response = client.post("/v1/dictionary/words", json=sample_word_data)
    word_id = create_response.json()["id"]

    # Get the word with full data (definitions, tags, etc.)
    response = client.get(f"/v1/dictionary/words/{word_id}?include_all=true")

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == word_id
    assert data["word_text"] == sample_word_data["word_text"]
    assert "definitions" in data


def test_get_nonexistent_word(client: TestClient) -> None:
    """Test getting a word that doesn't exist.

    Args:
        client: FastAPI test client
    """
    response = client.get("/v1/dictionary/words/99999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_update_word(client: TestClient, sample_word_data: dict[str, Any]) -> None:
    """Test updating an existing word.

    Args:
        client: FastAPI test client
        sample_word_data: Sample word data fixture
    """
    # Create a word
    create_response = client.post("/v1/dictionary/words", json=sample_word_data)
    word_id = create_response.json()["id"]

    # Update the word
    update_data = {"word_text": "updated_word"}
    response = client.patch(f"/v1/dictionary/words/{word_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == word_id
    assert data["word_text"] == "updated_word"
    assert data["language_code"] == sample_word_data["language_code"]  # Unchanged


def test_delete_word(client: TestClient, sample_word_data: dict[str, Any]) -> None:
    """Test deleting a word.

    Args:
        client: FastAPI test client
        sample_word_data: Sample word data fixture
    """
    # Create a word
    create_response = client.post("/v1/dictionary/words", json=sample_word_data)
    word_id = create_response.json()["id"]

    # Delete the word
    response = client.delete(f"/v1/dictionary/words/{word_id}")
    assert response.status_code == 204

    # Verify it's deleted
    get_response = client.get(f"/v1/dictionary/words/{word_id}")
    assert get_response.status_code == 404


def test_search_words(client: TestClient, sample_word_data: dict[str, Any]) -> None:
    """Test searching for words.

    Args:
        client: FastAPI test client
        sample_word_data: Sample word data fixture
    """
    # Create a word
    client.post("/v1/dictionary/words", json=sample_word_data)

    # Search with matching prefix
    response = client.get("/v1/dictionary/words?search=eph")

    assert response.status_code == 200
    data = response.json()

    assert len(data["data"]) == 1
    assert data["data"][0]["word_text"] == sample_word_data["word_text"]


def test_search_words_no_match(client: TestClient) -> None:
    """Test searching for words with no matches.

    Args:
        client: FastAPI test client
    """
    response = client.get("/v1/dictionary/words?search=nonexistent")

    assert response.status_code == 200
    data = response.json()

    assert len(data["data"]) == 0
    assert data["total"] == 0


def test_bulk_create_words(client: TestClient) -> None:
    """Test creating multiple words in one request.

    Args:
        client: FastAPI test client
    """
    words = [
        {"word_text": "ephemeral", "language_code": "en"},
        {"word_text": "ubiquitous", "language_code": "en"},
        {"word_text": "serendipity", "language_code": "en"},
    ]

    response = client.post("/v1/dictionary/words", json=words)

    assert response.status_code == 201
    data = response.json()

    assert len(data) == 3
    assert all("id" in word for word in data)
    assert all("created_at" in word for word in data)


# ============================================================================
# Definition Endpoints Tests
# ============================================================================


def test_create_definition(
    client: TestClient,
    sample_word_data: dict[str, Any],
    sample_definition_data: dict[str, Any],
) -> None:
    """Test creating a definition for a word.

    Args:
        client: FastAPI test client
        sample_word_data: Sample word data fixture
        sample_definition_data: Sample definition data fixture
    """
    # Create a word first
    word_response = client.post("/v1/dictionary/words", json=sample_word_data)
    word_id = word_response.json()["id"]

    # Create definition (word_id is in the URL, not the body)
    definition_body = {
        k: v for k, v in sample_definition_data.items() if k != "word_id"
    }

    # Create definition
    response = client.post(
        f"/v1/dictionary/words/{word_id}/definitions", json=definition_body
    )

    assert response.status_code == 201
    data = response.json()

    assert data["word_id"] == word_id
    assert data["definition_text"] == sample_definition_data["definition_text"]
    assert data["part_of_speech"] == sample_definition_data["part_of_speech"]
    assert "id" in data


def test_create_definition_for_nonexistent_word(
    client: TestClient, sample_definition_data: dict[str, Any]
) -> None:
    """Test creating a definition for a word that doesn't exist.

    Args:
        client: FastAPI test client
        sample_definition_data: Sample definition data fixture
    """
    # Create definition body without word_id (it's in the URL)
    definition_body = {
        k: v for k, v in sample_definition_data.items() if k != "word_id"
    }

    response = client.post(
        "/v1/dictionary/words/99999/definitions", json=definition_body
    )

    assert response.status_code == 404


# ============================================================================
# Tag Endpoints Tests
# ============================================================================


def test_create_tag(client: TestClient, sample_tag_data: dict[str, Any]) -> None:
    """Test creating a new tag.

    Args:
        client: FastAPI test client
        sample_tag_data: Sample tag data fixture
    """
    response = client.post("/v1/dictionary/tags", json=sample_tag_data)

    assert response.status_code == 201
    data = response.json()

    assert data["name"] == sample_tag_data["name"]
    assert data["description"] == sample_tag_data["description"]
    assert "id" in data


def test_create_duplicate_tag(
    client: TestClient, sample_tag_data: dict[str, Any]
) -> None:
    """Test creating a duplicate tag (should fail).

    Args:
        client: FastAPI test client
        sample_tag_data: Sample tag data fixture
    """
    # Create first tag
    response1 = client.post("/v1/dictionary/tags", json=sample_tag_data)
    assert response1.status_code == 201

    # Try to create duplicate
    response2 = client.post("/v1/dictionary/tags", json=sample_tag_data)
    assert response2.status_code == 400
    assert "already exists" in response2.json()["detail"]


def test_list_tags(client: TestClient, sample_tag_data: dict[str, Any]) -> None:
    """Test listing tags.

    Args:
        client: FastAPI test client
        sample_tag_data: Sample tag data fixture
    """
    # Create a tag
    client.post("/v1/dictionary/tags", json=sample_tag_data)

    # List tags
    response = client.get("/v1/dictionary/tags")

    assert response.status_code == 200
    data = response.json()

    assert len(data["data"]) == 1
    assert data["total"] == 1
    assert data["data"][0]["name"] == sample_tag_data["name"]


# ============================================================================
# Word-Tag Association Tests
# ============================================================================


def test_add_tag_to_word(
    client: TestClient,
    sample_word_data: dict[str, Any],
    sample_tag_data: dict[str, Any],
) -> None:
    """Test associating a tag with a word via update.

    Args:
        client: FastAPI test client
        sample_word_data: Sample word data fixture
        sample_tag_data: Sample tag data fixture
    """
    # Create word and tag
    word_response = client.post("/v1/dictionary/words", json=sample_word_data)
    word_id = word_response.json()["id"]

    tag_response = client.post("/v1/dictionary/tags", json=sample_tag_data)
    tag_name = tag_response.json()["name"]

    # Associate tag with word via update endpoint using tag name
    response = client.patch(
        f"/v1/dictionary/words/{word_id}", json={"tags": [tag_name]}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == word_id
    assert "tags" in data
    assert len(data["tags"]) == 1
    assert data["tags"][0]["name"] == tag_name


def test_get_word_with_tags(
    client: TestClient,
    sample_word_data: dict[str, Any],
    sample_tag_data: dict[str, Any],
) -> None:
    """Test getting a word with its tags.

    Args:
        client: FastAPI test client
        sample_word_data: Sample word data fixture
        sample_tag_data: Sample tag data fixture
    """
    # Create word and tag
    word_response = client.post("/v1/dictionary/words", json=sample_word_data)
    word_id = word_response.json()["id"]

    tag_response = client.post("/v1/dictionary/tags", json=sample_tag_data)
    tag_name = tag_response.json()["name"]

    # Associate tag with word via update using tag name
    client.patch(f"/v1/dictionary/words/{word_id}", json={"tags": [tag_name]})

    # Get word with tags using include_tags query param
    response = client.get(f"/v1/dictionary/words/{word_id}?include_tags=true")

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == word_id
    assert "tags" in data
    assert len(data["tags"]) == 1
    assert data["tags"][0]["name"] == sample_tag_data["name"]


# ============================================================================
# Tag Name Functionality Tests (Auto-create tags by name)
# ============================================================================


def test_create_word_with_tag_names_new_tags(client: TestClient) -> None:
    """Test creating a word with tag names that don't exist yet.

    Args:
        client: FastAPI test client
    """
    word_data = {
        "word_text": "doctor",
        "language_code": "en",
        "tags": ["medical", "profession"],
    }

    response = client.post("/v1/dictionary/words", json=word_data)

    assert response.status_code == 201
    data = response.json()

    assert data["word_text"] == "doctor"
    assert "tags" in data
    assert len(data["tags"]) == 2
    assert {tag["name"] for tag in data["tags"]} == {"medical", "profession"}


def test_create_word_with_tag_names_existing_tags(client: TestClient) -> None:
    """Test creating a word with tag names that already exist.

    Args:
        client: FastAPI test client
    """
    # Create tags first
    client.post(
        "/v1/dictionary/tags", json={"name": "medical", "description": "Medical terms"}
    )
    client.post(
        "/v1/dictionary/tags",
        json={"name": "informal", "description": "Informal usage"},
    )

    # Create word using existing tag names
    word_data = {
        "word_text": "doc",
        "language_code": "en",
        "tags": ["medical", "informal"],
    }

    response = client.post("/v1/dictionary/words", json=word_data)

    assert response.status_code == 201
    data = response.json()

    assert len(data["tags"]) == 2
    assert {tag["name"] for tag in data["tags"]} == {"medical", "informal"}

    # Verify tags weren't duplicated
    tags_response = client.get("/v1/dictionary/tags")
    assert tags_response.json()["total"] == 2


def test_create_word_with_mixed_new_and_existing_tags(client: TestClient) -> None:
    """Test creating a word with both new and existing tag names.

    Args:
        client: FastAPI test client
    """
    # Create one tag
    client.post(
        "/v1/dictionary/tags", json={"name": "medical", "description": "Medical terms"}
    )

    # Create word with mix of existing and new tags
    word_data = {
        "word_text": "stethoscope",
        "language_code": "en",
        "tags": ["medical", "equipment", "technical"],
    }

    response = client.post("/v1/dictionary/words", json=word_data)

    assert response.status_code == 201
    data = response.json()

    assert len(data["tags"]) == 3
    assert {tag["name"] for tag in data["tags"]} == {
        "medical",
        "equipment",
        "technical",
    }

    # Verify total tags in database
    tags_response = client.get("/v1/dictionary/tags")
    assert tags_response.json()["total"] == 3


def test_bulk_create_words_with_tag_names(client: TestClient) -> None:
    """Test bulk creating words with tag names.

    Args:
        client: FastAPI test client
    """
    words = [
        {
            "word_text": "doctor",
            "language_code": "en",
            "tags": ["medical", "profession"],
            "definitions": [
                {
                    "definition_text": "A person qualified to treat illness",
                    "part_of_speech": "noun",
                    "order": 0,
                    "examples": [
                        {"example_text": "I saw the doctor today", "source": None}
                    ],
                }
            ],
        },
        {
            "word_text": "nurse",
            "language_code": "en",
            "tags": ["medical", "profession", "healthcare"],
            "definitions": [
                {
                    "definition_text": "A person trained to care for the sick",
                    "part_of_speech": "noun",
                    "order": 0,
                    "examples": [],
                }
            ],
        },
    ]

    response = client.post("/v1/dictionary/words", json=words)

    assert response.status_code == 201
    data = response.json()

    assert len(data) == 2
    assert all("tags" in word for word in data)
    assert len(data[0]["tags"]) == 2
    assert len(data[1]["tags"]) == 3

    # Verify tags were created/reused correctly
    tags_response = client.get("/v1/dictionary/tags")
    assert tags_response.json()["total"] == 3  # medical, profession, healthcare


def test_update_word_with_tag_names(client: TestClient) -> None:
    """Test updating a word with tag names.

    Args:
        client: FastAPI test client
    """
    # Create word without tags
    word_data = {"word_text": "test", "language_code": "en"}
    create_response = client.post("/v1/dictionary/words", json=word_data)
    word_id = create_response.json()["id"]

    # Update with tags
    update_data = {"tags": ["category1", "category2"]}
    response = client.patch(f"/v1/dictionary/words/{word_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()

    assert len(data["tags"]) == 2
    assert {tag["name"] for tag in data["tags"]} == {"category1", "category2"}


def test_create_word_with_empty_tags_list(client: TestClient) -> None:
    """Test creating a word with empty tags list.

    Args:
        client: FastAPI test client
    """
    word_data = {
        "word_text": "simple",
        "language_code": "en",
        "tags": [],
    }

    response = client.post("/v1/dictionary/words", json=word_data)

    assert response.status_code == 201
    data = response.json()

    assert data["word_text"] == "simple"
    # Empty tags returns WordOut (no tags field), not WordFull
    assert "tags" not in data
