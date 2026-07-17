from typing import Any, Dict, List
from bson import ObjectId

from fastapi import APIRouter, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from db.mongodb import db_state

router = APIRouter()

def get_db() -> AsyncIOMotorDatabase:
    db = db_state.get("db")
    if db is None:
        print("CRITICAL ERROR: Database connection not found!")
        raise HTTPException(status_code=503, detail="Database not connected")
    return db

def _serialize_schedule(item: Dict[str, Any]) -> Dict[str, Any]:
    payload = dict(item)
    if "_id" in payload and payload["_id"] is not None:
        payload["_id"] = str(payload["_id"])
    return payload

@router.get("/schedules")
async def list_schedules() -> Dict[str, Any]:
    try:
        db = get_db()
        schedules = await db["schedules"].find({}).to_list(None)
        return {"schedules": [_serialize_schedule(item) for item in schedules]}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc

@router.post("/schedules", status_code=201)
async def create_schedule(payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        db = get_db()
        if isinstance(payload.get("schedules"), list):
            items = [item for item in payload["schedules"] if isinstance(item, dict)]
            if items:
                result = await db["schedules"].insert_many(items)
                return {"saved": len(result.inserted_ids), "schedules": items}
            return {"saved": 0, "schedules": []}

        result = await db["schedules"].insert_one(payload)
        payload["_id"] = str(result.inserted_id)
        return payload
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc

@router.put("/schedules/{schedule_id}")
async def update_schedule(schedule_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        db = get_db()
        payload.pop("_id", None)
        result = await db["schedules"].update_one({"_id": ObjectId(schedule_id)}, {"$set": payload})
        return {"updated": result.modified_count}
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid schedule id") from exc

@router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str) -> Dict[str, Any]:
    try:
        db = get_db()
        result = await db["schedules"].delete_one({"_id": ObjectId(schedule_id)})
        return {"deleted": result.deleted_count}
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid schedule id") from exc

@router.get("/classes")
async def list_classes() -> List[str]:
    try:
        db = get_db()
        courses = await db["processed_courses"].find({}, {"module": 1, "presentation": 1, "_id": 0}).to_list(None)
        return sorted({f"{course.get('module')}-{course.get('presentation')}" for course in courses})
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc

@router.get("/rooms")
async def list_rooms() -> List[str]:
    return [
        "G2-101",
        "G2-102",
        "G2-103",
        "G2-201",
        "G2-202",
        "G2-203",
        "E3-101",
        "E3-102",
        "E3-201",
        "E3-202",
        "E3-301",
        "E3-302",
        "B1-101",
        "B1-102",
        "B1-201",
        "B1-202",
        "Online - Zoom",
        "Online - Teams",
    ]