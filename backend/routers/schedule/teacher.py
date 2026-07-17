# ── schedule/teacher.py ───────────────────────────────────────────────────────
# Lên lịch dạy, lịch bù, danh sách phòng và lớp học
from typing import Any, Dict, List

from bson import ObjectId
from fastapi import APIRouter, HTTPException

from db.mongodb import db_state

router = APIRouter()


def get_db():
    db = db_state.get("db")
    if db is None or not db_state.get("connected", False):
        raise HTTPException(status_code=503, detail="Database not connected")
    return db


# ── Schedules ────────────────────────────────────────────────────────────────

@router.get("/schedules")
async def list_schedules(
    module: str | None = None,
    presentation: str | None = None,
) -> List[Dict[str, Any]]:
    try:
        db = get_db()
        query: Dict[str, Any] = {}
        if module:
            query["module"] = module
        if presentation:
            query["presentation"] = presentation
        return await db["schedules"].find(query).to_list(None)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc


@router.post("/schedules", status_code=201)
async def create_schedule(payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        db = get_db()
        result = await db["schedules"].insert_one(payload)
        payload["_id"] = str(result.inserted_id)
        return payload
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc


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
        raise HTTPException(status_code=400, detail="Invalid schedule id") from exc


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str) -> Dict[str, Any]:
    try:
        db = get_db()
        result = await db["schedules"].delete_one({"_id": ObjectId(schedule_id)})
        return {"deleted": result.deleted_count}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid schedule id") from exc


# ── Classes & Rooms ──────────────────────────────────────────────────────────

@router.get("/classes")
async def list_classes() -> List[str]:
    try:
        db = get_db()
        courses = await db["processed_courses"].find(
            {}, {"module": 1, "presentation": 1, "_id": 0}
        ).to_list(None)
        return sorted(
            {f"{c.get('module')}-{c.get('presentation')}" for c in courses}
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc


@router.get("/rooms")
async def list_rooms() -> List[str]:
    return [
        "G2-101", "G2-102", "G2-103", "G2-201", "G2-202", "G2-203",
        "E3-101", "E3-102", "E3-201", "E3-202", "E3-301", "E3-302",
        "B1-101", "B1-102", "B1-201", "B1-202",
        "Online - Zoom", "Online - Teams",
    ]
