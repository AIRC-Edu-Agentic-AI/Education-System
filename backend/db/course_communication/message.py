"""Message management functions."""

from bson import ObjectId
from bson.errors import InvalidId

from .constants import CHANNEL_TYPE_ANNOUNCEMENT, COURSE_STATUS_ARCHIVED
from .utils import now_iso, get_user_role, prepare_message_json
from .audit import record_audit
from .channel import get_channel


async def get_channel_messages(db, channel_id: str, parent_id: str | None = None):
    """Get all messages in a channel (optionally for a parent message)."""
    try:
        oid = ObjectId(channel_id)
    except InvalidId:
        return []
    query = {"channel_id": oid}
    if parent_id is None:
        query["parent_id"] = None
    else:
        try:
            query["parent_id"] = ObjectId(parent_id)
        except InvalidId:
            return []
    docs = await db.messages.find(query).sort("created_at", 1).to_list(length=200)
    return [prepare_message_json(doc) for doc in docs]


async def add_channel_message(db, channel_id: str, sender_id: int, content: str, parent_id: str | None = None):
    """Add a message to a channel."""
    channel = await get_channel(db, channel_id)
    if channel is None:
        raise ValueError("Channel not found")
    course = await db.courses.find_one({"course_code": channel.get("course_code")})
    if course is None:
        raise ValueError("Course not found")
    user_role = get_user_role(course, sender_id)
    if user_role is None:
        raise PermissionError("Sender is not enrolled in the course")
    if course.get("status") == COURSE_STATUS_ARCHIVED:
        raise PermissionError("Course communication is archived")

    if channel["type"] == CHANNEL_TYPE_ANNOUNCEMENT and parent_id is None and user_role not in channel.get("allowed_post_roles", []):
        raise PermissionError("Only instructors and class reps may create announcement posts")

    if channel["type"] == CHANNEL_TYPE_ANNOUNCEMENT and parent_id is not None:
        # comment on announcement thread is allowed for course members
        pass

    if channel["type"] != CHANNEL_TYPE_ANNOUNCEMENT and user_role not in channel.get("allowed_post_roles", []):
        raise PermissionError("User cannot post in this channel")

    msg = {
        "channel_id": ObjectId(channel_id),
        "course_code": channel.get("course_code"),
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
    await record_audit(db, "message_posted", channel.get("course_code"), sender_id, {"channel_id": channel_id, "message_id": str(result.inserted_id), "parent_id": parent_id})
    return prepare_message_json(await db.messages.find_one({"_id": result.inserted_id}))
