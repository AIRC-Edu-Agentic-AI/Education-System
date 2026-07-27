"""
Student Schedule Router.

BR09: Student chi xem lich hoc cua cac khoa hoc minh tham gia.
BR10: Lich hoc hien thi theo thong tin do giang vien quan ly.
BR11: Student duoc tao va cap nhat ke hoach tu hoc cua ban than.
BR12: Moi ke hoach tu hoc duoc gan voi 1 hoac nhieu khoa hoc.
"""

from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.mongodb import get_db
from db.mock_data import MOCK_SCHEDULE, MOCK_STUDY_PLAN

router = APIRouter()


# ── Pydantic Models ────────────────────────────────────────────────────────────

class StudySessionItem(BaseModel):
    subject: str
    type: str       # review | practice | assignment
    duration: int   # minutes
    day: str
    time: str
    sm2_interval: Optional[int] = 1


class StudyPlanUpdate(BaseModel):
    sessions: List[StudySessionItem]
    student_approved: Optional[bool] = True


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/{student_id}/weekly")
async def get_weekly_schedule(student_id: int):
    """
    BR09-10: Lay lich hoc co dinh cua sinh vien.
    """
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
    """Lay ke hoach tu hoc cua sinh vien."""
    db = get_db()
    if db is None:
        return MOCK_STUDY_PLAN
    doc = await db.study_plans.find_one({"student_id": student_id})
    return doc.get("sessions", MOCK_STUDY_PLAN) if doc else MOCK_STUDY_PLAN


@router.put("/{student_id}/plan")
async def update_study_plan(student_id: int, payload: StudyPlanUpdate):
    """
    BR11: Sinh vien cap nhat ke hoach tu hoc.
    BR20: Ke hoach do AI de xuat chi mang tinh ho tro — SV co quyen chinh sua.
    """
    db = get_db()
    if db is None:
        return {"ok": True, "mock": True}

    now = datetime.now(timezone.utc).isoformat()
    sessions = [s.dict() for s in payload.sessions]

    existing = await db.study_plans.find_one({"student_id": student_id})
    if existing:
        await db.study_plans.update_one(
            {"student_id": student_id},
            {"$set": {
                "sessions": sessions,
                "student_approved": payload.student_approved,
                "updated_at": now,
            }}
        )
    else:
        await db.study_plans.insert_one({
            "student_id": student_id,
            "sessions": sessions,
            "student_approved": payload.student_approved,
            "created_at": now,
            "updated_at": now,
        })

    return {"ok": True, "student_id": student_id, "session_count": len(sessions)}


@router.post("/{student_id}/plan/approve")
async def approve_study_plan(student_id: int):
    """SV xac nhan ke hoach do AI de xuat."""
    db = get_db()
    if db is None:
        return {"ok": True, "mock": True}
    await db.study_plans.update_one(
        {"student_id": student_id},
        {"$set": {"student_approved": True, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"ok": True, "student_id": student_id, "approved": True}