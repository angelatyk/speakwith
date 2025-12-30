from typing import Optional

from bson import ObjectId
from db.mongo import get_db

COLLECTION_NAME = "historical_figures"
db = get_db()


def find_by_name(person_name: str) -> Optional[dict]:
    """Find a historical figure by name (case-insensitive)."""
    return db[COLLECTION_NAME].find_one(
        {"person_name_lower": person_name.lower().strip()}
    )


def insert_figure(document: dict) -> dict:
    """Insert a new historical figure document into the collection."""
    result = db[COLLECTION_NAME].insert_one(document)
    document["_id"] = result.inserted_id
    return document


def update_figure(person_name: str, update: dict):
    """Update an existing historical figure by name."""
    return db[COLLECTION_NAME].update_one(
        {"person_name_lower": person_name.lower().strip()}, {"$set": update}
    )


def list_figures() -> list:
    """List all historical figures with minimal info."""
    return list(
        db[COLLECTION_NAME].find(
            {}, {"person_name": 1, "person_name_lower": 1, "created_at": 1}
        )
    )
