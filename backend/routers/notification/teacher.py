from fastapi import APIRouter
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel
from db.mongodb import get_db

router = APIRouter()

class NotificationCreate(BaseModel):
    senderRole: str
    receiverRole: str
    receiverId: Optional[int] = None
    receiverName: Optional[str] = None
    module: Optional[str] = None
    presentation: Optional[str] = None
    type: str
    title: str
    content: str
    priority: Optional[str] = "normal"

def serialize(doc):
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

@router.get("")
async def get_notifications():
    db = get_db()
    cursor = db.notifications.find({}).sort("created_at", -1)
    docs = await cursor.to_list(length=100)
    return [serialize(d) for d in docs]

@router.post("")
async def create_notification(notification: NotificationCreate):
    db = get_db()
    data = {
        "sender_id": None,
        "sender_role": notification.senderRole,
        "receiver_id": notification.receiverId,
        "receiver_name": notification.receiverName,
        "receiver_role": notification.receiverRole,
        "course_id": f"{notification.module}-{notification.presentation}" if notification.module else None,
        "type": notification.type,
        "priority": notification.priority,
        "payload": {
            "title": notification.title,
            "body": notification.content
        },
        "is_read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = await db.notifications.insert_one(data)
    data["_id"] = str(result.inserted_id)
    return data

@router.get("/attendance-stats/{module}/{presentation}")
async def get_attendance_stats(module: str, presentation: str):
    db = get_db()
    pipeline = [
        {"$match": {"code_module": module, "code_presentation": presentation}},
        {"$group": {"_id": "$final_result", "count": {"$sum": 1}}}
    ]
    raw = await db.processed_students.aggregate(pipeline).to_list(length=20)
    color_map = {
        "Pass": "#4CAF50",
        "Fail": "#F44336",
        "Withdrawn": "#FFC107",
        "Distinction": "#2196F3"
    }
    return [
        {"name": item["_id"] or "Unknown", "value": item["count"], "color": color_map.get(item["_id"], "#9E9E9E")}
        for item in raw
    ]

@router.get("/course/{module}/{presentation}")
async def get_course(module: str, presentation: str):
    db = get_db()
    course = await db.processed_courses.find_one({"module": module, "presentation": presentation}, {"_id": 0})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    cursor = db.processed_students.find({"code_module": module, "code_presentation": presentation}, {"_id": 0})
    students = await cursor.to_list(length=5000)
    return {**course, "students": students}
@router.get("/index")
async def get_index():
    db = get_db()
    cursor = db.processed_courses.find({}, {"students": 0, "_id": 0})
    courses = await cursor.to_list(length=500)
    result = []
    for c in courses:
        result.append({
            "module": c.get("module"),
            "module_name": c.get("module_name", c.get("name", "")),
            "presentation": c.get("presentation"),
            "presentation_name": c.get("presentation_name", ""),
            "num_weeks": c.get("num_weeks", 39),
            "course_length_days": c.get("num_weeks", 39) * 7,
            "student_count": c.get("student_count", 0)
        })
    return {"courses": result}
