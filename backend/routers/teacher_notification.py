from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import uuid
from bson import ObjectId

from db.mongodb import db_state
from db.utils import serialize_doc
from db.course_communication.channel import _ensure_course_channels
from db.course_communication.constants import CHANNEL_TYPE_ANNOUNCEMENT

router = APIRouter()

class BroadcastPayload(BaseModel):
    title: str
    content: str
    student_ids: Optional[List[int]] = None
    course_code: Optional[str] = None


class BroadcastPayload(BaseModel):
    student_ids: List[int]
    type: str
    title: str
    content: str
    course_code: str
    sender_role: str = "instructor"
    course_code: Optional[str] = None

@router.get("/notifications")
async def list_notifications(
    recipient_id: str,
    module: Optional[str] = None,
    presentation: Optional[str] = None,
    limit: int = 50,
):
    """
    List ALL notifications (Teacher Inbox and old logs).
    """
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

        if payload.student_ids:
            docs = [
                {
                    "student_id": sid,
                    "type": payload.type,
                    "read": False,
                    "sender_role": payload.senderRole,
                    "course_code": payload.course_code,
                    "payload": {"title": payload.title, "body": payload.content},
                    "created_at": now_iso,
                }
                for sid in payload.student_ids
            ]
            result = await db["notifications"].insert_many(docs)
            return {"ok": True, "count": len(result.inserted_ids)}

        new_doc = {
            "senderRole": payload.senderRole,
            "receiverRole": payload.receiverRole,
            "type": payload.type,
            "title": payload.title,
            "content": payload.content,
            "course_code": payload.course_code,
            "createdAt": now_iso,
        }
        result = await db["notifications"].insert_one(new_doc)
        new_doc["_id"] = str(result.inserted_id)
        return new_doc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.put("/notifications/{notif_id}")
async def update_notification(notif_id: str, payload: UpdateNotificationPayload) -> Dict[str, Any]:
    """Update an existing notification's title and/or content."""
    try:
        db = get_db()
        from bson import ObjectId
        from bson.errors import InvalidId

        try:
            oid = ObjectId(notif_id)
        except (InvalidId, TypeError):
            raise HTTPException(status_code=400, detail="Invalid notification ID")

        update_fields: Dict[str, Any] = {}
        if payload.title is not None:
            update_fields["title"] = payload.title
            # Also update nested payload.title for student-facing notifications
            update_fields["payload.title"] = payload.title
        if payload.content is not None:
            update_fields["content"] = payload.content
            update_fields["payload.body"] = payload.content
        update_fields["updatedAt"] = datetime.now(timezone.utc).isoformat()

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        result = await db["notifications"].update_one(
            {"_id": oid}, {"$set": update_fields}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Notification not found")

        updated = await db["notifications"].find_one({"_id": oid})
        return serialize_doc(updated)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.delete("/notifications/{notif_id}")
async def delete_notification(notif_id: str) -> Dict[str, Any]:
    """Delete a notification by ID."""
    try:
        db = get_db()
        from bson import ObjectId
        from bson.errors import InvalidId

        try:
            oid = ObjectId(notif_id)
        except (InvalidId, TypeError):
            raise HTTPException(status_code=400, detail="Invalid notification ID")

        result = await db["notifications"].delete_one({"_id": oid})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Notification not found")

        return {"ok": True, "deleted": notif_id}
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
                "course_code": payload.course_code,
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
