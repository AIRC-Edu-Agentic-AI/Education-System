from typing import Any, Dict, List
from bson import ObjectId

from fastapi import APIRouter, HTTPException

from db.mongodb import db_state
from db.utils import serialize_doc

router = APIRouter()


def get_db():
    db = db_state.get("db")
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    return db


@router.get("/schedules")
async def list_schedules() -> List[Dict[str, Any]]:
    try:
        db = get_db()
        docs = await db["schedules"].find({}).to_list(None)
        return serialize_doc(docs)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.post("/schedules", status_code=201)
async def create_schedule(payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        db = get_db()
        payload.pop("_id", None)
        new_schedule = payload.pop("newSchedule", None)
        
        if "schedules" in payload:
            await db["schedules"].delete_many({})
        result = await db["schedules"].insert_one(payload)
        payload["_id"] = str(result.inserted_id)

        if new_schedule and new_schedule.get("module") and new_schedule.get("presentation"):
            module = new_schedule["module"]
            presentation = new_schedule["presentation"]
            students = await db["processed_students"].find(
                {"code_module": module, "code_presentation": presentation},
                {"_id": 0}
            ).to_list(None)

            if students:
                from datetime import datetime, timezone
                now_iso = datetime.now(timezone.utc).isoformat()
                docs = [
                    {
                        "student_id": s.get("id_student", s.get("id")),
                        "type": "general",
                        "read": False,
                        "sender_role": "instructor",
                        "course_code": module,
                        "payload": {
                            "title": "New Class Scheduled",
                            "body": f"A new class \"{new_schedule.get('subject')}\" has been scheduled on {new_schedule.get('date')} at {new_schedule.get('startTime')}."
                        },
                        "created_at": now_iso,
                    }
                    for s in students
                ]
                if docs:
                    await db["notifications"].insert_many(docs)

        return serialize_doc(payload)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.put("/schedules/{schedule_id}")
async def update_schedule(schedule_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        db = get_db()
        payload.pop("_id", None)
        result = await db["schedules"].update_one(
            {"_id": ObjectId(schedule_id)}, {"$set": payload}
        )
        return {"updated": result.modified_count}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid schedule id: {exc}") from exc


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str) -> Dict[str, Any]:
    try:
        db = get_db()
        result = await db["schedules"].delete_one({"_id": ObjectId(schedule_id)})
        return {"deleted": result.deleted_count}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid schedule id: {exc}") from exc


@router.get("/classes")
async def list_classes() -> List[str]:
    try:
        db = get_db()
        courses = await db["processed_courses"].find(
            {}, {"module": 1, "presentation": 1, "_id": 0}
        ).to_list(None)
        return sorted({
            f"{c.get('module')}-{c.get('presentation')}"
            for c in courses
            if c.get("module") and c.get("presentation")
        })
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.get("/rooms")
async def list_rooms() -> List[str]:
    return [
        "G2-101", "G2-102", "G2-103",
        "G2-201", "G2-202", "G2-203",
        "E3-101", "E3-102",
        "E3-201", "E3-202", "E3-301", "E3-302",
        "B1-101", "B1-102", "B1-201", "B1-202",
        "Online - Zoom", "Online - Teams",
    ]
