from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
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
    student_ids: Optional[List[int]] = None
    type: str = "broadcast"
    
class DirectMessagePayload(BaseModel):
    student_id: int
    title: str
    content: str
    course_code: str
    sender_role: str = "instructor"

class UpdateNotificationPayload(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

@router.get("/notifications")
async def list_notifications(
    recipient_id: str = "teacher_admin",
    module: Optional[str] = None,
    presentation: Optional[str] = None,
    limit: int = 50,
):
    """
    List ALL notifications (Teacher Inbox and old logs) with backward compatibility.
    """
    db = db_state.get("db")
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
        
    # Query matching new recipient_id / is_broadcast_log or old senderRole / non-empty title
    # while filtering out raw machine-generated student warnings.
    base_conditions = [
        {"recipient_id": recipient_id},
        {"is_broadcast_log": True},
        {"senderRole": {"$exists": True}}
    ]
    
    if module and module != "ALL":
        # If module filter is active, require course_code/module matching along with base conditions
        query = {
            "$and": [
                {"$or": base_conditions},
                {"$or": [
                    {"course_code": module},
                    {"module": module}
                ]}
            ]
        }
    else:
        query = {"$or": base_conditions}
        
    docs = await db["notifications"].find(query).sort("createdAt", -1).sort("created_at", -1).limit(limit).to_list(None)
    
    serialized = serialize_doc(docs)
    
    # Map fields for backward compatibility with older UI schemas
    for doc in serialized:
        # Map created_at -> createdAt
        if "createdAt" not in doc and "created_at" in doc:
            doc["createdAt"] = doc["created_at"]
        elif "created_at" not in doc and "createdAt" in doc:
            doc["created_at"] = doc["createdAt"]
            
        # Map payload title/body if root title/content are missing
        if not doc.get("title") and doc.get("payload", {}).get("title"):
            doc["title"] = doc["payload"]["title"]
        if not doc.get("content") and doc.get("payload", {}).get("body"):
            doc["content"] = doc["payload"]["body"]
            
        # Default fallback fields
        if "senderRole" not in doc:
            doc["senderRole"] = "Instructor" if doc.get("sender_role") == "instructor" else doc.get("sender_role", "System")
        if "receiverRole" not in doc:
            doc["receiverRole"] = "Student"
            
    return serialized

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

    target_student_ids = payload.student_ids
    if not target_student_ids:
        parts = payload.course_code.split(' ', 1)
        if len(parts) == 2:
            module, presentation = parts
            students = await db["processed_students"].find(
                {"code_module": module, "code_presentation": presentation},
                {"_id": 0, "id_student": 1}
            ).to_list(None)
            target_student_ids = [s["id_student"] for s in students if "id_student" in s]
        else:
            target_student_ids = []

    # 3. Save a log for the teacher's UI that complies with the schema
    log_doc = {
        "student_id": 0,
        "type": payload.type,
        "read": True,
        "payload": {
            "title": payload.title,
            "body": payload.content
        },
        "created_at": now,
        "course_code": payload.course_code,
        "sender_role": payload.sender_role,
        "senderRole": "Instructor",
        "receiverRole": "Student",
        "is_broadcast_log": True,
        "target_count": len(target_student_ids),
        "recipient_id": "teacher_admin"
    }
    result = await db["notifications"].insert_one(log_doc)
    log_doc["_id"] = result.inserted_id
    
    # No need to save to singular notification collection since this is just a teacher log
    
    # 4. Insert student-facing notifications into both collections
    if target_student_ids:
        student_notis = [
            {
                "student_id": sid,
                "type": payload.type,
                "read": False,
                "sender_role": payload.sender_role,
                "payload": {
                    "title": payload.title,
                    "body": payload.content
                },
                "created_at": now,
                "course_code": payload.course_code
            }
            for sid in target_student_ids
        ]
        if student_notis:
            await db["notifications"].insert_many(student_notis)
            
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
        "created_at": now,
        "course_code": payload.course_code
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

@router.put("/notifications/{notif_id}")
async def update_notification(notif_id: str, payload: UpdateNotificationPayload) -> Dict[str, Any]:
    """Update an existing notification's title and/or content."""
    db = db_state.get("db")
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    try:
        oid = ObjectId(notif_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid notification ID")

    update_fields: Dict[str, Any] = {}
    if payload.title is not None:
        update_fields["title"] = payload.title
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

@router.delete("/notifications/{notif_id}")
async def delete_notification(notif_id: str) -> Dict[str, Any]:
    """Delete a notification by ID."""
    db = db_state.get("db")
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    try:
        oid = ObjectId(notif_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid notification ID")

    result = await db["notifications"].delete_one({"_id": oid})
        
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {"ok": True, "deleted": notif_id}