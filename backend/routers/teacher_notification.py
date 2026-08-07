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
    classroom_name: Optional[str] = None
    
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
        import re
        escaped_mod = re.escape(module)
        query = {
            "$and": [
                {"$or": base_conditions},
                {"$or": [
                    {"course_code": {"$regex": f"^{escaped_mod}", "$options": "i"}},
                    {"module": {"$regex": f"^{escaped_mod}", "$options": "i"}},
                    {"course_code": None},
                    {"course_code": {"$exists": False}},
                ]}
            ]
        }
    else:
        query = {"$or": base_conditions}
        
    docs = await db["notifications"].find(query).sort([("createdAt", -1), ("created_at", -1)]).limit(limit).to_list(None)
    
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

    # Sort descending by timestamp so newest notifications are ALWAYS first
    serialized.sort(key=lambda x: str(x.get("createdAt") or x.get("created_at") or ""), reverse=True)
            
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

    # Instant non-blocking WebSocket Push (< 10ms delivery)
    instant_noti = {
        "_id": str(ObjectId()),
        "type": payload.type,
        "read": False,
        "sender_role": payload.sender_role,
        "senderRole": "Instructor",
        "receiverRole": "Student",
        "course_code": payload.course_code,
        "payload": {
            "title": payload.title,
            "body": payload.content
        },
        "title": payload.title,
        "content": payload.content,
        "created_at": now,
        "createdAt": now,
        "is_broadcast_log": False
    }
    try:
        from routers.realtime_chat import manager
        import asyncio
        asyncio.create_task(manager.send_to_user("teacher_admin", {"type": "new_notification", "notification": {**instant_noti, "is_broadcast_log": True}}))
        if payload.student_ids:
            for sid in payload.student_ids:
                asyncio.create_task(manager.send_to_user(str(sid), {"type": "new_notification", "notification": {**instant_noti, "student_id": sid}}))
        for client_id in list(manager.active_connections.keys()):
            if client_id != "teacher_admin":
                asyncio.create_task(manager.send_to_user(client_id, {"type": "new_notification", "notification": instant_noti}))
    except Exception as e:
        print(f"Instant WS push error: {e}")
    
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
        course_clean = payload.course_code.strip()
        module = course_clean.split(' ')[0] # Lấy mã môn học gốc (VD: AAA từ "AAA 2013J")
        students = await db["students"].find(
            {"enrollments.code_module": module},
            {"_id": 0, "student_id": 1}
        ).to_list(None)
        target_student_ids = [s.get("student_id") for s in students if "student_id" in s]
        
        # Fallback to course members array if populated
        course_doc = await db["courses"].find_one({"course_code": course_clean})
        if course_doc and isinstance(course_doc.get("members"), list):
            member_ids = [m for m in course_doc["members"] if isinstance(m, int)]
            target_student_ids = list(set(target_student_ids + member_ids))

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
        "recipient_id": "teacher_admin",
        "classroom_name": payload.classroom_name,
    }
    result = await db["notifications"].insert_one(log_doc)
    log_doc["_id"] = result.inserted_id
    
    # 4. Insert student-facing notifications into collections
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
                "course_code": payload.course_code,
                "classroom_name": payload.classroom_name,
            }
            for sid in target_student_ids
        ]
        if student_notis:
            res_insert = await db["notifications"].insert_many(student_notis)
            for idx, inserted_id in enumerate(res_insert.inserted_ids):
                student_notis[idx]["_id"] = inserted_id
            
    return {"message": "Broadcast sent to channels and logged", "log": serialize_doc(log_doc)}

@router.post("/direct-message")
async def send_direct_message(payload: DirectMessagePayload, background_tasks: BackgroundTasks):
    db = db_state.get("db")
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Instant non-blocking WebSocket Push (< 10ms delivery)
    instant_noti = {
        "_id": str(ObjectId()),
        "student_id": payload.student_id,
        "type": "direct_message",
        "read": False,
        "sender_role": payload.sender_role,
        "senderRole": "Instructor",
        "receiverRole": "Student",
        "course_code": payload.course_code,
        "payload": {
            "title": payload.title,
            "body": payload.content
        },
        "title": payload.title,
        "content": payload.content,
        "created_at": now,
        "createdAt": now,
        "is_broadcast_log": False
    }
    try:
        from routers.realtime_chat import manager
        import asyncio
        asyncio.create_task(manager.send_to_user("teacher_admin", {"type": "new_notification", "notification": {**instant_noti, "is_broadcast_log": True}}))
        asyncio.create_task(manager.send_to_user(str(payload.student_id), {"type": "new_notification", "notification": instant_noti}))
    except Exception as e:
        print(f"Instant WS direct push error: {e}")

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
        "student_id": 0,
        "senderRole": "Instructor",
        "receiverRole": "Direct Student",
        "receiverId": payload.student_id,
        "type": "direct_message",
        "read": True,
        "title": payload.title,
        "content": payload.content,
        "payload": {
            "title": payload.title,
            "body": payload.content
        },
        "created_at": now,
        "is_broadcast_log": True,
        "target_count": 1,
        "course_code": payload.course_code,
        "recipient_id": "teacher_admin"
    }
    result = await db["notifications"].insert_one(log_doc)
    log_doc["_id"] = result.inserted_id

    return {"message": "Direct message sent", "log": serialize_doc(log_doc)}

@router.put("/notifications/{notif_id}")
async def update_notification(notif_id: str, payload: UpdateNotificationPayload) -> Dict[str, Any]:
    """Update an existing notification's title and/or content across all recipient copies."""
    db = db_state.get("db")
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    try:
        oid = ObjectId(notif_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid notification ID")

    target_doc = await db["notifications"].find_one({"_id": oid})
    if not target_doc:
        raise HTTPException(status_code=404, detail="Notification not found")

    created_at = target_doc.get("created_at") or target_doc.get("createdAt")
    old_title = target_doc.get("title") or target_doc.get("payload", {}).get("title")

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

    # Update teacher log doc
    await db["notifications"].update_one({"_id": oid}, {"$set": update_fields})

    # Update all matching student notification docs by title or created_at
    or_clauses = []
    if old_title:
        or_clauses.append({"title": old_title})
        or_clauses.append({"payload.title": old_title})
    if created_at:
        or_clauses.append({"created_at": created_at})
        or_clauses.append({"createdAt": created_at})
        
    if or_clauses:
        await db["notifications"].update_many({"$or": or_clauses}, {"$set": update_fields})

    updated = await db["notifications"].find_one({"_id": oid})
    serialized_updated = serialize_doc(updated)

    # Broadcast real-time WebSocket update to all open clients
    try:
        from routers.realtime_chat import manager
        import asyncio
        for client_id in list(manager.active_connections.keys()):
            asyncio.create_task(manager.send_to_user(client_id, {
                "type": "notification_updated",
                "notification": serialized_updated,
                "created_at": created_at,
                "title": old_title,
                "new_title": payload.title or old_title
            }))
    except Exception as e:
        print(f"WebSocket update push error: {e}")

    return serialized_updated


@router.delete("/notifications/{notif_id}")
async def delete_notification(notif_id: str) -> Dict[str, Any]:
    """Delete a notification by ID and purge all matching student copies in MongoDB."""
    db = db_state.get("db")
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    try:
        oid = ObjectId(notif_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid notification ID")

    target_doc = await db["notifications"].find_one({"_id": oid})
    if not target_doc:
        raise HTTPException(status_code=404, detail="Notification not found")

    created_at = target_doc.get("created_at") or target_doc.get("createdAt")
    doc_title = target_doc.get("title") or target_doc.get("payload", {}).get("title")
    doc_body = target_doc.get("content") or target_doc.get("payload", {}).get("body")

    # Delete target doc
    await db["notifications"].delete_one({"_id": oid})

    # Purge all matching student copies in MongoDB
    or_clauses = []
    if doc_title:
        or_clauses.append({"title": doc_title})
        or_clauses.append({"payload.title": doc_title})
    if created_at:
        or_clauses.append({"created_at": created_at})
        or_clauses.append({"createdAt": created_at})

    if or_clauses:
        await db["notifications"].delete_many({"$or": or_clauses})

    # Broadcast real-time WebSocket delete event to all open clients
    try:
        from routers.realtime_chat import manager
        import asyncio
        delete_event = {
            "type": "notification_deleted",
            "notification_id": notif_id,
            "created_at": created_at,
            "title": doc_title,
            "content": doc_body
        }
        for client_id in list(manager.active_connections.keys()):
            asyncio.create_task(manager.send_to_user(client_id, delete_event))
    except Exception as e:
        print(f"WebSocket delete push error: {e}")

    return {"ok": True, "deleted": notif_id}