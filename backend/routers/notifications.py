from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import re

from fastapi import APIRouter
from pydantic import BaseModel
from db.mongodb import get_db
from db.mock_data import MOCK_NOTIFICATIONS

router = APIRouter()


def _normalize_notification_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(doc)
    payload = normalized.get("payload") if isinstance(normalized.get("payload"), dict) else {}

    title = normalized.get("title") or payload.get("title") or ""
    body = normalized.get("content") or payload.get("body") or ""
    if title or body:
        payload = {**payload, "title": title or payload.get("title", ""), "body": body or payload.get("body", "")}
        normalized["payload"] = payload

    if "title" not in normalized and payload.get("title"):
        normalized["title"] = payload["title"]
    if "content" not in normalized and payload.get("body"):
        normalized["content"] = payload["body"]

    if "created_at" not in normalized:
        normalized["created_at"] = normalized.get("createdAt") or datetime.now(timezone.utc).isoformat()
    if "createdAt" not in normalized:
        normalized["createdAt"] = normalized["created_at"]

    if "read" not in normalized:
        normalized["read"] = normalized.get("is_read", False)
    if "action_options" not in normalized:
        normalized["action_options"] = []
    if "type" not in normalized:
        normalized["type"] = "general"

    if "student_id" not in normalized:
        for field in ("receiverId", "receiver_id", "recipient_id", "studentId"):
            value = normalized.get(field)
            if isinstance(value, int):
                normalized["student_id"] = value
                break

    return normalized


def _course_code_matches(stored_code: Optional[str], requested_code: Optional[str]) -> bool:
    if not stored_code or not requested_code:
        return False
    stored = re.sub(r"\s+", " ", str(stored_code).strip()).lower()
    requested = re.sub(r"\s+", " ", str(requested_code).strip()).lower()
    if stored == requested:
        return True
    return stored.startswith(requested) or requested.startswith(stored)


def _build_notification_query(student_id: int | None, unread_only: bool, now_iso: str, course_code: str | None = None):
    conditions: List[Dict[str, Any]] = []

    if student_id is not None:
        conditions.append({
            "$or": [
                {"student_id": student_id},
                {"receiverId": student_id},
                {"receiver_id": student_id},
                {"recipient_id": student_id},
                {"studentId": student_id},
                {"receiverRole": {"$regex": "^(student|students|all)$", "$options": "i"}},
            ]
        })

    if unread_only:
        conditions.append({
            "$or": [
                {"read": False},
                {"read": {"$exists": False}},
                {"is_read": False},
                {"is_read": {"$exists": False}},
            ]
        })

    if course_code is not None:
        conditions.append({
            "$or": [
                {"course_code": course_code},
                {"courseCode": course_code},
            ]
        })

    conditions.append({
        "$or": [
            {"send_at": {"$exists": False}},
            {"send_at": {"$lte": now_iso}},
        ]
    })

    if not conditions:
        return {}
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}


@router.get("/{student_id}")
async def get_notifications(student_id: int, unread_only: bool = True):
    db = get_db()
    if db is None:
        notifs = MOCK_NOTIFICATIONS
        if unread_only:
            notifs = [n for n in notifs if not n["read"]]
        return notifs

    now_iso = datetime.now(timezone.utc).isoformat()
    query = _build_notification_query(student_id, unread_only, now_iso)
    cursor = db["notifications"].find(query).sort("created_at", -1).limit(20)
    docs = await cursor.to_list(length=20)
    normalized_docs = []
    for d in docs:
        d["_id"] = str(d["_id"])
        normalized_docs.append(_normalize_notification_doc(d))
    return normalized_docs


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
    await db["notifications"].update_one(
        {"_id": oid}, {"$set": {"read": True, "is_read": True}}
    )
    return {"ok": True}


# ── Broadcast (Teacher → Students) ───────────────────────────────────────────

class BroadcastPayload(BaseModel):
    student_ids: List[int]          # danh sách student_id nhận thông báo
    type: str                       # "academic_warning" | "general" | "assignment" | ...
    title: str
    content: str
    sender_role: str = "instructor"
    course_code: Optional[str] = None


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
            "course_code": payload.course_code,
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
        result = await db["notifications"].insert_many(docs)
        return {"ok": True, "count": len(result.inserted_ids)}

    return {"ok": True, "count": 0}


@router.get("/course/{course_code}")
async def get_course_notifications(course_code: str, student_id: int):
    """
    Get notifications for a specific student in a specific course.
    """
    db = get_db()
    if db is None:
        return []

    now_iso = datetime.now(timezone.utc).isoformat()
    course_code_clauses = [
        {"course_code": course_code},
        {"courseCode": course_code},
        {"course_code": {"$regex": f"^{re.escape(course_code)}", "$options": "i"}},
        {"courseCode": {"$regex": f"^{re.escape(course_code)}", "$options": "i"}},
    ]
    student_filter = {
        "$or": [
            {"student_id": student_id},
            {"receiverId": student_id},
            {"receiverRole": {"$regex": "^(student|students|all)$", "$options": "i"}},
        ]
    }
    query = {
        "$and": [
            {"$or": course_code_clauses},
            {"$and": [student_filter, {"is_broadcast_log": {"$ne": True}}]},
            {
                "$or": [
                    {"send_at": {"$exists": False}},
                    {"send_at": {"$lte": now_iso}},
                ]
            }
        ]
    }

    cursor = db["notifications"].find(query).sort("created_at", -1).limit(50)
    docs = await cursor.to_list(length=50)
    if not docs:
        # Fallback only if query returns nothing, still keep student filtering.
        all_docs = await db["notifications"].find({}).sort("created_at", -1).limit(200).to_list(length=200)
        docs = [
            doc for doc in all_docs
            if _course_code_matches(doc.get("course_code") or doc.get("courseCode"), course_code)
            and doc.get("is_broadcast_log") is not True
            and (
                doc.get("student_id") == student_id
                or doc.get("receiverId") == student_id
                or isinstance(doc.get("receiverRole"), str)
                   and re.match(r"^(student|students|all)$", doc.get("receiverRole"), re.IGNORECASE)
            )
        ]
    normalized_docs = []
    for d in docs:
        d["_id"] = str(d["_id"])
        normalized_docs.append(_normalize_notification_doc(d))
    return normalized_docs


