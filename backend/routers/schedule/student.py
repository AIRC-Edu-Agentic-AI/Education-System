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

def _day_label(date_str: str) -> str:
    """Convert ISO date string (YYYY-MM-DD) to day label (Mon, Tue, ...)."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][dt.weekday()]
    except Exception:
        return ""


def _schedule_item_to_week_item(item: dict) -> dict:
    """Convert a teacher ScheduleItem dict into a WeekItem dict for the student app."""
    subject = item.get("subject") or item.get("activity") or "Class"
    date_str = item.get("date") or ""
    start_time = item.get("startTime") or ""
    end_time = item.get("endTime") or ""
    room = item.get("room") or item.get("locationUrl") or ""

    day = _day_label(date_str) if date_str else ""
    time_part = start_time if start_time else ""
    room_part = f" · {room}" if room else ""
    subtitle = f"{day}, {time_part}{room_part}" if day else f"{date_str} {time_part}{room_part}".strip()

    date_time = None
    if date_str and start_time:
        try:
            date_time = datetime.strptime(f"{date_str} {start_time}", "%Y-%m-%d %H:%M").isoformat()
        except Exception:
            pass
    if date_time is None and date_str:
        try:
            date_time = datetime.strptime(date_str, "%Y-%m-%d").isoformat()
        except Exception:
            date_time = datetime.now(timezone.utc).isoformat()

    return {
        "title": subject,
        "subtitle": subtitle,
        "date_time": date_time or datetime.now(timezone.utc).isoformat(),
        "is_completed": item.get("status") == "completed",
        "is_urgent": item.get("is_urgent", False),
    }


@router.get("/{student_id}/weekly")
async def get_weekly_schedule(student_id: int):
    """
    BR09-10: Lay lich hoc co dinh cua sinh vien.
    Query schedules by the student's enrolled modules/presentations
    so teacher-created schedules appear in the student timetable.
    """
    db = get_db()
    empty_schedule = {
        "current_week": 7,
        "total_weeks": 30,
        "streak_days": 0,
        "lectures": [],
        "classes": [],
        "assignments": [],
        "exams": [],
    }

    if db is None:
        return empty_schedule

    # 1. Find the student's enrollments
    student_doc = await db.students.find_one(
        {"student_id": student_id},
        {"_id": 0, "enrollments": 1}
    )
    enrollments = student_doc.get("enrollments", []) if student_doc else []

    if not enrollments:
        return empty_schedule

    # 2. Build set of (module, presentation) pairs
    enrolled_pairs = set()
    for e in enrollments:
        m = e.get("code_module")
        p = e.get("code_presentation")
        if m and p:
            enrolled_pairs.add((m, p))
        elif m:
            enrolled_pairs.add((m, None))

    if not enrolled_pairs:
        return empty_schedule

    # 3. Collect schedule items from timetable_blocks (teacher-dashboard bulk save)
    all_items = []
    timetable_docs = await db.timetable_blocks.find({}).to_list(None)
    for doc in timetable_docs:
        schedules_list = doc.get("schedules")
        if isinstance(schedules_list, list):
            for item in schedules_list:
                if not isinstance(item, dict):
                    continue
                item_module = item.get("module")
                item_pres = item.get("presentation")
                if not item_module:
                    continue
                for (em, ep) in enrolled_pairs:
                    if item_module == em and (ep is None or item_pres == ep):
                        all_items.append(item)
                        break
        else:
            # Flat doc (single schedule)
            item_module = doc.get("module")
            item_pres = doc.get("presentation")
            if item_module:
                for (em, ep) in enrolled_pairs:
                    if item_module == em and (ep is None or item_pres == ep):
                        clean = {k: v for k, v in doc.items() if k != "_id"}
                        all_items.append(clean)
                        break

    # 4. Also collect from 'schedules' collection (schedule/teacher.py)
    for (em, ep) in enrolled_pairs:
        query = {"module": em}
        if ep:
            query["presentation"] = ep
        sched_docs = await db.schedules.find(query).to_list(None)
        for doc in sched_docs:
            schedules_list = doc.get("schedules")
            if isinstance(schedules_list, list):
                for item in schedules_list:
                    if isinstance(item, dict):
                        item_module = item.get("module")
                        item_pres = item.get("presentation")
                        if item_module == em and (ep is None or item_pres == ep):
                            all_items.append(item)
            else:
                clean = {k: v for k, v in doc.items() if k != "_id"}
                all_items.append(clean)

    # 5. Convert items to WeeklySchedule format
    lectures = []
    classes = []

    seen_ids = set()
    for item in all_items:
        item_id = item.get("id") or f"{item.get('date')}_{item.get('startTime')}_{item.get('subject')}"
        if item_id in seen_ids:
            continue
        seen_ids.add(item_id)

        # Skip cancelled schedules
        if item.get("status") == "cancelled":
            continue

        week_item = _schedule_item_to_week_item(item)

        # Classify: activities with "lab", "tutorial", "class" go to classes; rest to lectures
        activity = (item.get("activity") or item.get("subject") or "").lower()
        if any(kw in activity for kw in ("lab", "tutorial", "class", "practical", "workshop")):
            classes.append(week_item)
        else:
            lectures.append(week_item)

    return {
        "current_week": 7,
        "total_weeks": 30,
        "streak_days": 0,
        "lectures": lectures,
        "classes": classes,
        "assignments": [],
        "exams": [],
    }


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