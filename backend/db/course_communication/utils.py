"""Utility functions for course communication module."""

import datetime
from datetime import timezone


def now_iso() -> str:
    """Get current time in ISO 8601 format."""
    return datetime.datetime.now(timezone.utc).isoformat()


def to_json(doc: dict) -> dict:
    """Convert MongoDB document to JSON, converting ObjectId to string."""
    if doc is None:
        return None
    doc = dict(doc)
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

