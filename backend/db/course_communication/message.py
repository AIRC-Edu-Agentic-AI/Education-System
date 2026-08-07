"""Message management functions."""

from bson import ObjectId
from bson.errors import InvalidId

from .constants import CHANNEL_TYPE_ANNOUNCEMENT, COURSE_STATUS_ARCHIVED, COURSE_STATUS_DELETED
from .utils import now_iso, get_user_role, prepare_message_json, to_json
from .audit import record_audit
from .channel import get_channel


async def get_channel_messages(db, channel_id: str, parent_id: str | None = None):
    """Get all messages in a channel (optionally for a parent message)."""
    channel_query = [{"channel_id": channel_id}]
    try:
        channel_query.append({"channel_id": ObjectId(channel_id)})
    except Exception:
        pass
        
    query = {"$or": channel_query}
    if parent_id is None:
        query["parent_id"] = None
    else:
        parent_query = [{"parent_id": parent_id}]
        try:
            parent_query.append({"parent_id": ObjectId(parent_id)})
        except Exception:
            pass
        query["$or"] = [{"$and": [q, p]} for q in channel_query for p in parent_query]

    docs = await db.messages.find(query).sort("created_at", 1).to_list(length=200)
    return [prepare_message_json(doc) for doc in docs]


async def add_channel_message(db, channel_id: str, sender_id: int, content: str, parent_id: str | None = None, course_code: str | None = None, channel_type: str | None = None):
    """Add a message to a channel."""
    channel = await get_channel(db, channel_id)
    if channel is None and (channel_type == "private_message" or str(channel_id).startswith("private_")):
        from routers.realtime_chat import get_private_channel
        chan_doc = await get_private_channel(str(sender_id), course_code)
        channel_id = chan_doc["id"]
        channel = await get_channel(db, channel_id)
    if channel is None and course_code:
        from .channel import _ensure_course_channels
        await _ensure_course_channels(db, course_code)
        query = {"course_code": course_code, "status": {"$ne": COURSE_STATUS_DELETED}}
        if channel_type:
            query["type"] = channel_type
        fallback_channel = await db.channels.find_one(query)
        if fallback_channel is not None:
            channel = to_json(fallback_channel)
    if channel is None:
        raise ValueError("Channel not found")

    channel_type_actual = channel.get("type", "discussion")
    course_code_key = channel.get("course_code")
    course = await db.courses.find_one({"$or": [{"course_code": course_code_key}, {"code_module": course_code_key}]})
    if course is None:
        course = {"course_code": course_code_key, "instructors": [], "members": []}
    user_role = get_user_role(course, sender_id)
    if user_role is None:
        user_role = "student" if isinstance(sender_id, int) and sender_id > 0 else "instructor"

    if course.get("status") == COURSE_STATUS_ARCHIVED:
        raise PermissionError("Course communication is archived")

    # ── Permission check ─────────────────────────────────────────────────────
    # For discussion / private_message / class_group channels: all roles may post
    # For announcement channels: only instructors and class reps may create threads;
    #   anyone may reply in a thread (parent_id is not None)
    if channel_type_actual == CHANNEL_TYPE_ANNOUNCEMENT:
        if parent_id is None and user_role not in ("instructor", "class_rep"):
            raise PermissionError("Only instructors and class reps may create announcement posts")
        # Replies in announcement thread are allowed for all enrolled members – fall through
    # All other channel types (discussion, private_message, class_group, etc.) allow any role
    # ─────────────────────────────────────────────────────────────────────────

    resolved_channel_id = channel.get("_id")
    if isinstance(resolved_channel_id, str):
        try:
            resolved_channel_id = ObjectId(resolved_channel_id)
        except InvalidId:
            resolved_channel_id = ObjectId(channel_id)
    elif resolved_channel_id is None:
        resolved_channel_id = ObjectId(channel_id)

    msg = {
        "channel_id": resolved_channel_id,
        "course_code": channel.get("course_code"),
        "channel_type": channel_type_actual,
        "sender_id": sender_id,
        "sender_role": user_role,
        "content": content,
        "created_at": now_iso(),
        "parent_id": None,
        "reactions": [],
    }
    if parent_id is not None:
        try:
            msg["parent_id"] = ObjectId(parent_id)
        except InvalidId:
            raise ValueError("Invalid parent_id")
    result = await db.messages.insert_one(msg)
    await record_audit(db, "message_posted", channel.get("course_code"), sender_id, {"channel_id": str(resolved_channel_id), "message_id": str(result.inserted_id), "parent_id": parent_id})
    return prepare_message_json(await db.messages.find_one({"_id": result.inserted_id}))
