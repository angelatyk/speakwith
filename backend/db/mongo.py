import os
from typing import Optional

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

_MONGO_CLIENT: Optional[MongoClient] = None

# MongoDB connection
# Default to localhost:27017 if MONGO_URI is not set
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "talkwith")


def get_client() -> MongoClient:
    """
    Return a singleton MongoDB client.
    """
    global _MONGO_CLIENT

    if _MONGO_CLIENT is None:
        _MONGO_CLIENT = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,
        )

    return _MONGO_CLIENT


def get_db():
    """
    Return the configured MongoDB database.
    """
    client = get_client()
    return client[DATABASE_NAME]


def check_connection() -> bool:
    """
    Verify MongoDB connectivity.
    """
    try:
        client = get_client()
        client.admin.command("ping")
        return True
    except Exception:
        return False
