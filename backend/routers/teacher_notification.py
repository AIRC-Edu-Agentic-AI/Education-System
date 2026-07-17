from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from db.mongodb import db_state

router = APIRouter()

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

def get_db() -> AsyncIOMotorDatabase:
    if not db_state.get("db"):
        raise HTTPException(status_code=503, detail="Database not connected")
    return db_state["db"]

@router.get("/notifications")
async def list_notifications() -> List[Dict[str, Any]]:
    try:
        db = get_db()
        return await db["notifications"].find({}).sort("createdAt", -1).to_list(None)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc

@router.post("/notifications", status_code=201)
async def create_notification(payload: NotificationPayload) -> Dict[str, Any]:
    try:
        db = get_db()
        now_iso = datetime.now(timezone.utc).isoformat()

        if payload.student_ids:
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
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc

@router.post("/broadcast", status_code=201)
async def broadcast_notification(payload: BroadcastPayload) -> Dict[str, Any]:
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
