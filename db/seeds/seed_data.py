"""Seed database with vocabulary data.

Usage:
    python db/seeds/seed_data.py
    python db/seeds/seed_data.py --file custom_data.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import httpx


def load_json_file(file_path: Path) -> list[dict[str, Any]]:
    """Load JSON data from file.

    Args:
        file_path: Path to JSON file

    Returns:
        List of word dictionaries

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Seed file not found: {file_path}")

    with file_path.open(encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("JSON file must contain an array of words")

    return data


def seed_from_json(
    file_path: Path, base_url: str = "http://localhost:8000/v1/dictionary/words"
) -> int:
    """Seed database from JSON file with upsert behavior.

    Args:
        file_path: Path to JSON seed file
        base_url: API endpoint URL

    Returns:
        Number of words created or updated
    """
    words = load_json_file(file_path)

    if not words:
        print("No words to seed")
        return 0

    print(f"Seeding {len(words)} words from {file_path.name}...")

    created = 0
    updated = 0
    unchanged = 0

    with httpx.Client(timeout=60.0) as client:
        for word in words:
            word_text = word.get("word_text", "unknown")
            lang = word.get("language_code", "en")

            try:
                # Check if word exists
                get_url = f"{base_url}/{lang}/{word_text}?include_all=true"
                get_resp = client.get(get_url)

                if get_resp.status_code == 404:
                    # Word doesn't exist - create it
                    post_resp = client.post(base_url, json=word)
                    if post_resp.status_code == 201:
                        created += 1
                        print(f"  + {word_text}")
                    else:
                        print(f"  x {word_text} - {post_resp.json()}")
                elif get_resp.status_code == 200:
                    # Word exists - check if update needed
                    existing = get_resp.json()
                    if _needs_update(existing, word):
                        patch_url = f"{base_url}/{existing['id']}"
                        patch_resp = client.patch(patch_url, json=word)
                        if patch_resp.status_code == 200:
                            updated += 1
                            print(f"  ~ {word_text} (updated)")
                        else:
                            print(f"  x {word_text} - {patch_resp.json()}")
                    else:
                        unchanged += 1
                        print(f"  = {word_text} (unchanged)")
                else:
                    print(f"  x {word_text} - {get_resp.json()}")
            except httpx.HTTPError as e:
                print(f"  x {word_text} - Error: {e}")

    print(f"Done: {created} created, {updated} updated, {unchanged} unchanged")
    return created + updated


def _needs_update(existing: dict[str, Any], seed: dict[str, Any]) -> bool:
    """Check if existing word differs from seed data."""
    # Compare definitions
    existing_defs = {d["definition_text"] for d in existing.get("definitions", [])}
    seed_defs = {d["definition_text"] for d in seed.get("definitions", [])}
    if existing_defs != seed_defs:
        return True

    # Compare tags
    existing_tags = {t["name"] for t in existing.get("tags", [])}
    seed_tags = set(seed.get("tags", []))
    if existing_tags != seed_tags:
        return True

    # Compare word forms
    existing_forms = {f["form_text"] for f in existing.get("word_forms", [])}
    seed_forms = {f["form_text"] for f in seed.get("word_forms", [])}
    if existing_forms != seed_forms:
        return True

    return False


def seed_wicked_vocabulary(api_url: str = "http://localhost:8000/v1/dictionary/words") -> int:
    """Seed Wicked musical vocabulary.

    Args:
        api_url: API endpoint URL

    Returns:
        Number of words seeded
    """
    seed_file = Path(__file__).parent / "wicked_vocabulary.json"
    return seed_from_json(seed_file, api_url)


def main() -> None:
    """Main entry point for seeding script."""
    # Parse command line args
    if len(sys.argv) > 1 and sys.argv[1] == "--file":
        if len(sys.argv) < 3:
            print("Error: --file requires a filename")
            sys.exit(1)
        file_path = Path(sys.argv[2])
    else:
        # Default to wicked_vocabulary.json
        file_path = Path(__file__).parent / "wicked_vocabulary.json"

    try:
        seed_from_json(file_path)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}")
        sys.exit(1)
    except httpx.HTTPError as e:
        print(f"API Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
