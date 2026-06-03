from fastapi import APIRouter
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
