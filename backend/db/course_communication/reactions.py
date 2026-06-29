"""Message reaction functions."""

from bson import ObjectId
from bson.errors import InvalidId

from .utils import now_iso, get_user_role
from .audit import record_audit


async def react_to_message(db, message_id: str, user_id: int, emoji: str):
    """Add a reaction to a message."""
    try:
        mid = ObjectId(message_id)
    except InvalidId:
        return False
    message = await db.messages.find_one({"_id": mid})
    if message is None:
        return False
    course = await db.courses.find_one({"course_code": message.get("course_code")})
    if course is None or get_user_role(course, user_id) is None:
        raise PermissionError("User is not a course member")
    reaction = {
        "user_id": user_id,
        "emoji": emoji,
        "created_at": now_iso(),
    }
    await db.messages.update_one(
        {"_id": mid},
        {"$addToSet": {"reactions": reaction}},
    )
    await record_audit(db, "message_reacted", course.get("course_code"), user_id, {"message_id": message_id, "emoji": emoji})
    return True
