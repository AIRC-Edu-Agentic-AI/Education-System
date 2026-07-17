"""Helpers for serializing MongoDB documents to JSON-safe dicts."""
from bson import ObjectId
from datetime import datetime
from typing import Any


def serialize_doc(doc: Any) -> Any:
    """Recursively convert ObjectId / datetime to str so FastAPI can JSON-encode."""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    if isinstance(doc, dict):
        return {k: serialize_doc(v) for k, v in doc.items()}
    if isinstance(doc, ObjectId):
        return str(doc)
    if isinstance(doc, datetime):
        return doc.isoformat()
    return doc
