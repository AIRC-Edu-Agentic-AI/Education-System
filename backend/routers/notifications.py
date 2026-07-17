from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel
from db.mongodb import get_db
from db.mock_data import MOCK_NOTIFICATIONS

router = APIRouter()

@router.get("/{student_id}")
async def get_notifications(student_id: int, unread_only: bool = True):
    db = get_db()
    if db is None:
        notifs = MOCK_NOTIFICATIONS
        if unread_only:
            notifs = [n for n in notifs if not n["read"]]
        return notifs

    query = {"student_id": student_id}
    if unread_only:
        query["read"] = False
    # Dispatcher: hide notifications scheduled for later (send_at in the future).
    # Missing send_at = immediate (backward compatible).
    now_iso = datetime.now(timezone.utc).isoformat()
    query["$or"] = [
        {"send_at": {"$exists": False}},
        {"send_at": {"$lte": now_iso}},
    ]
    cursor = db.notifications.find(query).sort("created_at", -1).limit(20)
    docs = await cursor.to_list(length=20)
    for d in docs:
        d["_id"] = str(d["_id"])
    # When connected, return real notifications (empty list is valid — no mock fallback)
    return docs

@router.patch("/{notif_id}/read")
async def mark_read(notif_id: str):
    db = get_db()
    if db is None:
        return {"ok": True}
    from bson import ObjectId
    from bson.errors import InvalidId
    try:
        oid = ObjectId(notif_id)
    except (InvalidId, TypeError):
        # Non-ObjectId id (e.g. a mock/string id) — nothing to update
        return {"ok": True}
    await db.notifications.update_one(
        {"_id": oid}, {"$set": {"read": True}}
    )
    return {"ok": True}


# ── Broadcast (Teacher → Students) ───────────────────────────────────────────

class BroadcastPayload(BaseModel):
    student_ids: List[int]          # danh sách student_id nhận thông báo
    type: str                       # "academic_warning" | "general" | "assignment" | ...
    title: str
    content: str
    sender_role: str = "instructor"


@router.post("/broadcast", status_code=201)
async def broadcast_notification(payload: BroadcastPayload) -> Dict[str, Any]:
    """
    Teacher gửi thông báo tới một hoặc nhiều sinh viên.
    Ghi đúng schema để student app (Flutter) đọc được qua GET /notify/{student_id}.
    """
    db = get_db()
    now_iso = datetime.now(timezone.utc).isoformat()

    docs = [
        {
            "student_id": sid,
            "type": payload.type,
            "read": False,
            "sender_role": payload.sender_role,
            "payload": {
                "title": payload.title,
                "body": payload.content,
            },
            "created_at": now_iso,
        }
        for sid in payload.student_ids
    ]

    if db is None:
        # Mock mode — không persist, trả về danh sách mock
        return {"ok": True, "count": len(docs), "mock": True}

    if docs:
        result = await db.notifications.insert_many(docs)
        return {"ok": True, "count": len(result.inserted_ids)}

    return {"ok": True, "count": 0}

