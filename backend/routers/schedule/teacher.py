from fastapi import APIRouter, HTTPException
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel
from db.mongodb import get_db

router = APIRouter()

class ScheduleCreate(BaseModel):
    module: str
    presentation: str
    week: int
    date: str
    startTime: str
    endTime: str
    subject: str
    className: str
    teacher: str
    room: Optional[str] = ""
    status: Optional[str] = "scheduled"
    isMakeup: Optional[bool] = False
    note: Optional[str] = ""
    changeLog: Optional[list] = []

class ScheduleUpdate(BaseModel):
    module: Optional[str] = None
    presentation: Optional[str] = None
    week: Optional[int] = None
    date: Optional[str] = None
    startTime: Optional[str] = None
    endTime: Optional[str] = None
    subject: Optional[str] = None
    className: Optional[str] = None
    teacher: Optional[str] = None
    room: Optional[str] = None
    status: Optional[str] = None
    isMakeup: Optional[bool] = None
    note: Optional[str] = None
    changeLog: Optional[list] = None

def serialize(doc):
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

@router.get("")
async def get_schedules(module: Optional[str] = None, presentation: Optional[str] = None):
    db = get_db()
    query = {}
    if module:
        query["module"] = module
    if presentation:
        query["presentation"] = presentation
    cursor = db.timetable_blocks.find(query)
    docs = await cursor.to_list(length=500)
    return [serialize(d) for d in docs]

@router.post("")
async def create_schedule(schedule: ScheduleCreate):
    db = get_db()
    data = schedule.model_dump()
    data["createdAt"] = datetime.now(timezone.utc).isoformat()
    result = await db.timetable_blocks.insert_one(data)
    data["_id"] = str(result.inserted_id)

    notification = {
        "sender_id": None,
        "sender_role": "system",
        "receiver_id": None,
        "receiver_role": "class",
        "course_id": f"{schedule.module}-{schedule.presentation}",
        "type": "class_schedule",
        "priority": "normal",
        "payload": {
            "title": f"New class scheduled: {schedule.subject}",
            "body": f"Date: {schedule.date}, Time: {schedule.startTime}-{schedule.endTime}, Room: {schedule.room}"
        },
        "is_read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(notification)

    return data

@router.put("/{schedule_id}")
async def update_schedule(schedule_id: str, schedule: ScheduleUpdate):
    db = get_db()
    try:
        oid = ObjectId(schedule_id)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=400, detail="Invalid schedule ID")

    update_data = {k: v for k, v in schedule.model_dump().items() if v is not None}
    update_data["updatedAt"] = datetime.now(timezone.utc).isoformat()

    result = await db.timetable_blocks.update_one(
        {"_id": oid},
        {"$set": update_data}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Schedule not found")

    notification = {
        "sender_id": None,
        "sender_role": "system",
        "receiver_id": None,
        "receiver_role": "class",
        "type": "schedule_update",
        "priority": "high",
        "payload": {
            "title": "Class schedule updated",
            "body": f"Schedule {schedule_id} has been updated."
        },
        "is_read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(notification)

    return {"updated": result.modified_count}

@router.delete("/{schedule_id}")
async def delete_schedule(schedule_id: str):
    db = get_db()
    try:
        oid = ObjectId(schedule_id)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=400, detail="Invalid schedule ID")

    result = await db.timetable_blocks.delete_one({"_id": oid})
    return {"deleted": result.deleted_count}

@router.get("/classes")
async def get_classes():
    db = get_db()
    cursor = db.processed_courses.find({}, {"module": 1, "presentation": 1, "_id": 0})
    docs = await cursor.to_list(length=500)
    classes = list(set(f"{d['module']}-{d['presentation']}" for d in docs if "module" in d and "presentation" in d))
    return classes

@router.get("/rooms")
async def get_rooms():
    return [
        "G2-101", "G2-102", "G2-103", "G2-201", "G2-202", "G2-203",
        "E3-101", "E3-102", "E3-201", "E3-202", "E3-301", "E3-302",
        "B1-101", "B1-102", "B1-201", "B1-202",
        "Online - Zoom", "Online - Teams"
    ]