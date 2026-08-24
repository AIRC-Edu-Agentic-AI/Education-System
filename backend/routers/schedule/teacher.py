# ── schedule/teacher.py ───────────────────────────────────────────────────────
# Lên lịch dạy, lịch bù, danh sách phòng và lớp học
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException

from db.mongodb import db_state

router = APIRouter()


# ── Conflict Detection ────────────────────────────────────────────────────────

def _to_minutes(time_str: Optional[str]) -> Optional[int]:
    """Convert 'HH:MM' string to total minutes. Returns None if invalid."""
    if not time_str or ':' not in time_str:
        return None
    try:
        h, m = time_str.split(':', 1)
        return int(h) * 60 + int(m)
    except ValueError:
        return None


def _overlaps(start_a: Optional[int], end_a: Optional[int],
              start_b: Optional[int], end_b: Optional[int]) -> bool:
    """Return True if time interval [start_a, end_a) overlaps [start_b, end_b)."""
    if any(v is None for v in (start_a, end_a, start_b, end_b)):
        return False
    return start_a < end_b and start_b < end_a  # type: ignore[operator]


async def detect_conflicts(
    db,
    payload: Dict[str, Any],
    exclude_id: Optional[str] = None,
) -> List[str]:
    """
    Query all active (non-cancelled) schedules on the same date and detect
    teacher / class / room overlaps with *payload*.

    :param db: Motor AsyncIOMotorDatabase instance.
    :param payload: The schedule being created or updated.
    :param exclude_id: _id (string) of the document being updated — excluded
                       from the conflict search so a record doesn't conflict
                       with itself.
    :returns: List of human-readable conflict messages (empty = no conflicts).
    """
    date = payload.get("date")
    start = _to_minutes(payload.get("startTime"))
    end = _to_minutes(payload.get("endTime"))
    teacher = (payload.get("teacher") or "").strip()
    class_name = (payload.get("className") or "").strip()
    room = (payload.get("room") or "").strip()

    # Need at least date + times to check overlap
    if not date or start is None or end is None:
        return []

    query: Dict[str, Any] = {
        "date": date,
        "status": {"$ne": "cancelled"},
    }
    if exclude_id:
        try:
            query["_id"] = {"$ne": ObjectId(exclude_id)}
        except Exception:
            pass  # ignore invalid ObjectId format

    existing = await db["schedules"].find(query).to_list(None)

    errors: List[str] = []
    for other in existing:
        other_start = _to_minutes(other.get("startTime"))
        other_end = _to_minutes(other.get("endTime"))
        if not _overlaps(start, end, other_start, other_end):
            continue

        other_teacher = (other.get("teacher") or "").strip()
        other_class = (other.get("className") or "").strip()
        other_room = (other.get("room") or "").strip()
        time_desc = f"{payload.get('startTime')}-{payload.get('endTime')} on {date}"

        if teacher and teacher == other_teacher:
            errors.append(
                f"Teacher conflict: '{teacher}' already has a session at {time_desc}."
            )
        if class_name and class_name == other_class:
            errors.append(
                f"Class conflict: '{class_name}' already has a session at {time_desc}."
            )
        # Only flag room conflicts for physical rooms (skip online)
        if room and not room.lower().startswith("online") and room == other_room:
            errors.append(
                f"Room conflict: '{room}' is already booked at {time_desc}."
            )

    return list(dict.fromkeys(errors))  # deduplicate while preserving order


def get_db():
    if not db_state.get("db"):
        raise HTTPException(status_code=503, detail="Database not connected")
    return db_state["db"]


from routers.teacher_schedule import notify_students, notify_students_deleted


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

        # ── Conflict detection ────────────────────────────────────────────────
        conflicts = await detect_conflicts(db, payload)
        if conflicts:
            raise HTTPException(
                status_code=409,
                detail={"message": "Schedule conflicts detected.", "conflicts": conflicts},
            )
        # ─────────────────────────────────────────────────────────────────────

        result = await db["schedules"].insert_one(payload)
        payload["_id"] = str(result.inserted_id)
        await notify_students(payload, None, "schedule:create")
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

        # ── Conflict detection (exclude current document from check) ──────────
        conflicts = await detect_conflicts(db, payload, exclude_id=schedule_id)
        if conflicts:
            raise HTTPException(
                status_code=409,
                detail={"message": "Schedule conflicts detected.", "conflicts": conflicts},
            )
        # ─────────────────────────────────────────────────────────────────────

        original = await db["schedules"].find_one({"_id": ObjectId(schedule_id)})
        result = await db["schedules"].update_one(
            {"_id": ObjectId(schedule_id)}, {"$set": payload}
        )
        updated = await db["schedules"].find_one({"_id": ObjectId(schedule_id)})
        await notify_students(updated or payload, original, "schedule:update")
        return {"updated": result.modified_count}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid schedule id") from exc


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str) -> Dict[str, Any]:
    try:
        db = get_db()
        doc = await db["schedules"].find_one({"_id": ObjectId(schedule_id)})
        result = await db["schedules"].delete_one({"_id": ObjectId(schedule_id)})
        if doc:
            await notify_students_deleted(doc)
        else:
            await notify_students_deleted({"_id": schedule_id})
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
