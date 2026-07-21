"""Channel management functions."""

from bson import ObjectId
from .constants import (
    CHANNEL_TYPE_ANNOUNCEMENT,
    CHANNEL_TYPE_DISCUSSION,
    COURSE_STATUS_ACTIVE,
    COURSE_STATUS_DELETED,
    ANNOUNCEMENT_CHANNEL,
    DISCUSSION_CHANNEL,
)
from .utils import now_iso, to_json


async def _ensure_course_channels(db, course_code: str):
    """Ensure a course has the required channels."""
    existing = await db.channels.find({"course_code": course_code, "status": {"$ne": COURSE_STATUS_DELETED}}).to_list(length=10)
    existing_types = {c.get("type") for c in existing}
    now = now_iso()
    to_insert = []
    if CHANNEL_TYPE_ANNOUNCEMENT not in existing_types:
        to_insert.append({
            **ANNOUNCEMENT_CHANNEL,
            "course_code": course_code,
            "status": COURSE_STATUS_ACTIVE,
            "created_at": now,
            "updated_at": now,
        })
    if CHANNEL_TYPE_DISCUSSION not in existing_types:
        to_insert.append({
            **DISCUSSION_CHANNEL,
            "course_code": course_code,
            "status": COURSE_STATUS_ACTIVE,
            "created_at": now,
            "updated_at": now,
        })
    if to_insert:
        await db.channels.insert_many(to_insert)


async def get_course_channels(db, course_code: str):
    """Get all channels for a course, creating the default ones if missing."""
    await _ensure_course_channels(db, course_code)
    docs = await db.channels.find({"course_code": course_code, "status": {"$ne": COURSE_STATUS_DELETED}}).sort("type", 1).to_list(length=20)
    return [to_json(doc) for doc in docs]


async def get_channel(db, channel_id: str):
    """Get channel by ID."""
    from bson.errors import InvalidId
    try:
        oid = ObjectId(channel_id)
    except InvalidId:
        return None
    channel = await db.channels.find_one({"_id": oid})
    return to_json(channel)
