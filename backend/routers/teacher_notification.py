from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.mongodb import db_state
from db.utils import serialize_doc

router = APIRouter()


class NotificationPayload(BaseModel):
    senderRole: str
    receiverRole: str
    type: str
    title: str
    content: str
    student_ids: Optional[List[int]] = None


class BroadcastPayload(BaseModel):
    student_ids: List[int]
    type: str
    title: str
    content: str
    sender_role: str = "instructor"


def get_db():
    db = db_state.get("db")
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    return db


@router.get("/notifications")
async def list_notifications() -> List[Dict[str, Any]]:
    try:
        db = get_db()
        docs = await db["notifications"].find({}).sort("createdAt", -1).to_list(None)
        return serialize_doc(docs)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.post("/notifications", status_code=201)
async def create_notification(payload: NotificationPayload) -> Dict[str, Any]:
    try:
        db = get_db()
        now_iso = datetime.now(timezone.utc).isoformat()

        # Nếu có student_ids -> ghi thông báo riêng cho từng sinh viên
        if payload.student_ids:
            docs = [
                {
                    "student_id": sid,
                    "type": payload.type,
                    "read": False,
                    "sender_role": payload.senderRole,
                    "payload": {"title": payload.title, "body": payload.content},
                    "created_at": now_iso,
                }
                for sid in payload.student_ids
            ]
            result = await db["notifications"].insert_many(docs)
            return {"ok": True, "count": len(result.inserted_ids)}

        # Thông báo chung
        new_doc = {
            "senderRole": payload.senderRole,
            "receiverRole": payload.receiverRole,
            "type": payload.type,
            "title": payload.title,
            "content": payload.content,
            "createdAt": now_iso,
        }
        result = await db["notifications"].insert_one(new_doc)
        new_doc["_id"] = str(result.inserted_id)
        return new_doc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.post("/broadcast", status_code=201)
async def broadcast_notification(payload: BroadcastPayload) -> Dict[str, Any]:
    try:
        db = get_db()
        now_iso = datetime.now(timezone.utc).isoformat()
        docs = [
            {
                "student_id": sid,
                "type": payload.type,
                "read": False,
                "sender_role": payload.sender_role,
                "payload": {"title": payload.title, "body": payload.content},
                "created_at": now_iso,
            }
            for sid in payload.student_ids
        ]
        if docs:
            result = await db["notifications"].insert_many(docs)
            return {"ok": True, "count": len(result.inserted_ids)}
        return {"ok": True, "count": 0}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc
