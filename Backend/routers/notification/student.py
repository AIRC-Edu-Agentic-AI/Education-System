# ── notification/student.py ───────────────────────────────────────────────────
# Student-facing notification endpoints (read & mark-read).
# These mirror the logic in routers/notifications.py but are organized
# under the notification/ package for cleaner structure.
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from db.mongodb import db_state
from db.mock_data import MOCK_NOTIFICATIONS

router = APIRouter()


def get_db():
    return db_state.get("db")


@router.get("/{student_id}")
async def get_notifications(student_id: int, unread_only: bool = True) -> List[Dict[str, Any]]:
    """Get notifications for a student."""
    db = get_db()
    if db is None:
        notifs = MOCK_NOTIFICATIONS
        if unread_only:
            notifs = [n for n in notifs if not n["read"]]
        return notifs

    query: Dict[str, Any] = {"student_id": student_id}
    if unread_only:
        query["read"] = False

    now_iso = datetime.now(timezone.utc).isoformat()
    query["$or"] = [
        {"send_at": {"$exists": False}},
        {"send_at": {"$lte": now_iso}},
    ]

    cursor = db.notifications.find(query).sort("created_at", -1).limit(20)
    docs = await cursor.to_list(length=20)
    for d in docs:
        d["_id"] = str(d["_id"])
    return docs


@router.patch("/{notif_id}/read")
async def mark_read(notif_id: str) -> Dict[str, Any]:
    """Mark a notification as read."""
    db = get_db()
    if db is None:
        return {"ok": True}
    from bson import ObjectId
    from bson.errors import InvalidId
    try:
        oid = ObjectId(notif_id)
    except (InvalidId, TypeError):
        return {"ok": True}
    await db.notifications.update_one(
        {"_id": oid}, {"$set": {"read": True}}
    )
    return {"ok": True}
