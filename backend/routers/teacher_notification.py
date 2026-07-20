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
    course_code: str
    sender_role: str = "instructor"
    
class DirectMessagePayload(BaseModel):
    student_id: int
    title: str
    content: str
    course_code: str
    sender_role: str = "instructor"

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
        
    query = {"$or": [{"recipient_id": recipient_id}, {"is_broadcast_log": True}]}
    if module:
        query["$or"].append({"course_code": module})
        query["$or"].append({"module": module})
        
    docs = await db["notifications"].find(query).sort("created_at", -1).limit(limit).to_list(None)
    return {"notifications": serialize_doc(docs)}

@router.post("/broadcast")
async def send_broadcast(payload: BroadcastPayload, background_tasks: BackgroundTasks):
    db = db_state.get("db")
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    # 1. Ensure announcement channel exists for this course
    await _ensure_course_channels(db, payload.course_code)
    
    channel = await db["channels"].find_one({
        "course_code": payload.course_code,
        "type": CHANNEL_TYPE_ANNOUNCEMENT
    })
    
    if not channel:
        raise HTTPException(status_code=404, detail="Announcement channel not found")

    now = datetime.now(timezone.utc).isoformat()
    
    # 2. Insert into messages collection (for student chat UI)
    msg_doc = {
        "channel_id": channel["_id"],
        "course_code": payload.course_code,
        "sender_id": "teacher_admin",
        "sender_role": payload.sender_role,
        "content": f"**{payload.title}**\n\n{payload.content}",
        "created_at": now,
        "parent_id": None,
        "reactions": []
    }
    await db["messages"].insert_one(msg_doc)

    # 3. Save a log for the teacher's old NotificationManager UI
    log_doc = {
        "senderRole": "Instructor",
        "receiverRole": "Student",
        "type": "broadcast",
        "title": payload.title,
        "content": payload.content,
        "createdAt": now,
        "is_broadcast_log": True,
        "target_count": 0,
        "course_code": payload.course_code
    }
    result = await db["notifications"].insert_one(log_doc)
    log_doc["_id"] = result.inserted_id
    
    return {"message": "Broadcast sent to channels and logged", "log": serialize_doc(log_doc)}

@router.post("/direct-message")
async def send_direct_message(payload: DirectMessagePayload, background_tasks: BackgroundTasks):
    db = db_state.get("db")
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Notify student
    student_noti = {
        "student_id": payload.student_id,
        "type": "direct_message",
        "read": False,
        "sender_role": payload.sender_role,
        "payload": {
            "title": payload.title,
            "body": payload.content
        },
        "created_at": now
    }
    await db["notifications"].insert_one(student_noti)
    
    # Log for teacher
    log_doc = {
        "senderRole": "Instructor",
        "receiverRole": "Direct Student",
        "receiverId": payload.student_id,
        "type": "direct_message",
        "title": payload.title,
        "content": payload.content,
        "createdAt": now,
        "is_broadcast_log": True,
        "target_count": 1,
        "course_code": payload.course_code
    }
    result = await db["notifications"].insert_one(log_doc)
    log_doc["_id"] = result.inserted_id
    
    return {"message": "Direct message sent", "log": serialize_doc(log_doc)}