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


def get_user_role(course: dict, user_id: int) -> str | None:
    """Get user role in a course."""
    if user_id in course.get("instructors", []):
        return "instructor"
    if user_id in course.get("class_reps", []):
        return "class_rep"
    if user_id in course.get("members", []):
        return "student"
    return None


def prepare_message_json(doc: dict) -> dict:
    """Prepare message document for JSON response."""
    doc = to_json(doc)
    if doc.get("parent_id") is not None:
        doc["parent_id"] = str(doc["parent_id"])
    if isinstance(doc.get("reactions"), list):
        doc["reactions"] = [dict(r) for r in doc["reactions"]]
    return doc
