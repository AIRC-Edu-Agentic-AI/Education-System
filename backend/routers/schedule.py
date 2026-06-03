# ── schedule.py ───────────────────────────────────────────────────────────────
from fastapi import APIRouter
from db.mongodb import get_db
from db.mock_data import MOCK_SCHEDULE, MOCK_STUDY_PLAN

router = APIRouter()

@router.get("/{student_id}/weekly")
async def get_weekly_schedule(student_id: int):
    db = get_db()
    if db is None:
        return MOCK_SCHEDULE
    doc = await db.timetable_blocks.find_one({"student_id": student_id})
    if not doc:
        return MOCK_SCHEDULE
    doc.pop("_id", None)
    return doc

@router.get("/{student_id}/plan")
async def get_study_plan(student_id: int):
    db = get_db()
    if db is None:
        return MOCK_STUDY_PLAN
    doc = await db.study_plans.find_one({"student_id": student_id})
    return doc.get("sessions", MOCK_STUDY_PLAN) if doc else MOCK_STUDY_PLAN