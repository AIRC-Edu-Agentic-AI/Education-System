# ── notification/teacher.py ───────────────────────────────────────────────────
# Gửi thông báo, cảnh báo học tập — Teacher
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.mongodb import db_state

router = APIRouter()


def get_db():
    db = db_state.get("db")
    if db is None or not db_state.get("connected", False):
        raise HTTPException(status_code=503, detail="Database not connected")
    return db


def _normalize_notification(item: Dict[str, Any]) -> Dict[str, Any]:
    payload = dict(item)
    payload["_id"] = str(payload.get("_id", "")) if payload.get("_id") is not None else None

    if payload.get("student_id") is not None:
        payload["senderRole"] = payload.get("sender_role") or "Instructor"
        payload["receiverRole"] = "Student"
        payload["title"] = payload.get("payload", {}).get("title") or payload.get("title") or "New message"
        payload["content"] = payload.get("payload", {}).get("body") or payload.get("content") or ""
        payload["createdAt"] = payload.get("created_at") or payload.get("createdAt") or datetime.now(timezone.utc).isoformat()
        payload["type"] = payload.get("type") or "General Notice"
        return payload

    payload["senderRole"] = payload.get("senderRole") or payload.get("sender_role") or "Instructor"
    payload["receiverRole"] = payload.get("receiverRole") or payload.get("receiver_role") or "Student"
    payload["title"] = payload.get("title") or payload.get("payload", {}).get("title") or "New message"
    payload["content"] = payload.get("content") or payload.get("payload", {}).get("body") or ""
    payload["createdAt"] = payload.get("createdAt") or payload.get("created_at") or datetime.now(timezone.utc).isoformat()
    payload["type"] = payload.get("type") or "General Notice"
    return payload


# ── Models ───────────────────────────────────────────────────────────────────

class NotificationPayload(BaseModel):
    senderRole: str
    receiverRole: str
    type: str
    title: str
    content: str
    student_ids: Optional[List[int]] = None  # nếu có → ghi schema student app


class BroadcastPayload(BaseModel):
    student_ids: List[int]          # danh sách student_id nhận thông báo
    type: str                       # "academic_warning" | "general" | "assignment" | ...
    title: str
    content: str
    sender_role: str = "instructor"


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/notifications")
async def list_notifications() -> List[Dict[str, Any]]:
    """Teacher xem danh sách thông báo đã gửi."""
    try:
        db = get_db()
        items = await db["notifications"].find({}).sort("createdAt", -1).to_list(None)
        return [_normalize_notification(item) for item in items]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc


@router.post("/notifications", status_code=201)
async def create_notification(payload: NotificationPayload) -> Dict[str, Any]:
    """
    Gửi thông báo (backward compatible).
    Nếu có student_ids → ghi schema student app để Flutter đọc được.
    """
    try:
        db = get_db()
        now_iso = datetime.now(timezone.utc).isoformat()

        if payload.student_ids:
            # Ghi schema chuẩn để student app đọc được
            docs = [
                {
                    "student_id": sid,
                    "type": payload.type,
                    "read": False,
                    "sender_role": payload.senderRole,
                    "payload": {
                        "title": payload.title,
                        "body": payload.content,
                    },
                    "created_at": now_iso,
                }
                for sid in payload.student_ids
            ]
            result = await db["notifications"].insert_many(docs)
            return {"ok": True, "count": len(result.inserted_ids)}

        # Không có student_ids → ghi schema cũ (teacher broadcast chung)
        new_notification = {
            "senderRole": payload.senderRole,
            "receiverRole": payload.receiverRole,
            "type": payload.type,
            "title": payload.title,
            "content": payload.content,
            "createdAt": now_iso,
        }
        result = await db["notifications"].insert_one(new_notification)
        new_notification["_id"] = str(result.inserted_id)
        return new_notification
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc


@router.post("/broadcast", status_code=201)
async def broadcast_notification(payload: BroadcastPayload) -> Dict[str, Any]:
    """
    Gửi thông báo tới danh sách sinh viên với đúng schema để
    student app (Flutter) đọc được qua GET /notify/{student_id}.
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
        return {"ok": True, "count": len(docs), "mock": True}

    if docs:
        result = await db["notifications"].insert_many(docs)
        return {"ok": True, "count": len(result.inserted_ids)}

    return {"ok": True, "count": 0}
