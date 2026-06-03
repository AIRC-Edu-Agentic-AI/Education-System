"""
Demo seed script — populates MongoDB Atlas with data tuned to trigger every agentic behaviour.

Run from backend/ directory with the project venv active:
    python db/seed.py

What gets triggered by a single POST /debug/trigger/event_check:
    1. Deadline warning       — TMA-02 due in 3 days
    2. Assessment shock       — TMA-01 score 42% < 50%  → O2 Course Planning
    3. VLE inactivity         — 4 days inactive
    4. Milestone overdue x2  — m2 (in_progress) and m3 (pending) past due date
    5. Risk > 0.7             — O1 Risk Intervention → O3 + Course Planner + Weekly Planner
    6. Risk > 0.8             — Wellbeing Agent

Chat intents also demonstrated:
    - "giải thích hồi quy tuyến tính" → tutoring → update_knowledge_state
    - "kết quả học tập của tôi"        → performance → O3 analysis
    - "nên học môn gì tiếp theo"       → recommendation → get_course_recommendations
    - "tôi đang căng thẳng"            → wellbeing → empathetic response
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# ── Config ─────────────────────────────────────────────────────────────────────
load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI", "")
MONGODB_DB  = os.getenv("MONGODB_DB", "student_agent_db")
STUDENT_ID  = 28400

# Current module day approximation: week 7, mid-week → day 46
CURRENT_DAY = 46


# ── Data ───────────────────────────────────────────────────────────────────────

STUDENT = {
    "auth0_id": "auth0|demo_28400",
    "student_id": STUDENT_ID,
    "full_name": "Nguyễn Văn An",
    "short_name": "Văn An",
    "demographics": {
        "gender": "M",
        "age_band": "25-35",
        "region": "Hà Nội",
        "highest_education": "HE Qualification",
        "imd_band": "20-30%",
        "disability": False,
        "num_prev_attempts": 0,
        "studied_credits": 60,
    },
    "enrollments": [
        # ── PRIMARY: at-risk course — drives the whole demo ──────────────────
        {
            "code_module": "DATA201",
            "code_presentation": "2024A",
            "title": "Phân tích Dữ liệu & Thống kê",
            "module_length": 30,
            "registration_date": -15,
            "unregistration_date": None,
            "final_result": None,
            "assessments": [
                # TMA-01: submitted but LOW SCORE → triggers assessment_shock → O2
                {
                    "id_assessment": 1752,
                    "type": "TMA",
                    "due_date": 19,
                    "weight": 10,
                    "score": 42,          # < 50 → assessment_shock
                    "submitted_date": 18,
                    "is_banked": False,
                },
                # TMA-02: NOT submitted, due in 3 days → deadline_warning + milestones
                {
                    "id_assessment": 1753,
                    "type": "TMA",
                    "due_date": 49,       # CURRENT_DAY + 3 → deadline_warning
                    "weight": 25,
                    "score": None,
                    "submitted_date": None,
                    "is_banked": False,
                },
                {
                    "id_assessment": 1754,
                    "type": "CMA",
                    "due_date": 68,
                    "weight": 15,
                    "score": None,
                    "submitted_date": None,
                    "is_banked": False,
                },
                {
                    "id_assessment": 1755,
                    "type": "Exam",
                    "due_date": 261,
                    "weight": 50,
                    "score": None,
                    "submitted_date": None,
                    "is_banked": False,
                },
            ],
            "vle_summary": {
                "total_clicks": 3842,
                "last_active_day": 42,    # CURRENT_DAY - 4 → vle_inactivity (> 3 days)
                "by_activity_type": {
                    "resource": 1240, "forumng": 287,
                    "oucontent": 1100, "quiz": 420,
                    "url": 312, "homepage": 483,
                },
                # Declining trend (weeks 1–7) — pairs with rising risk history
                "weekly_clicks": [
                    320, 410, 380, 300, 210, 120, 45,
                    *([0] * 23),
                ],
            },
        },
        # ── Đại số Tuyến tính — mixed performance ────────────────────────────
        {
            "code_module": "MATH102",
            "code_presentation": "2024A",
            "title": "Đại số Tuyến tính",
            "module_length": 30,
            "registration_date": -15,
            "unregistration_date": None,
            "final_result": None,
            "assessments": [
                {"id_assessment": 2010, "type": "TMA", "due_date": 22,
                 "weight": 20, "score": 65, "submitted_date": 21, "is_banked": False},
                {"id_assessment": 2011, "type": "CMA", "due_date": 55,
                 "weight": 30, "score": 58, "submitted_date": 54, "is_banked": False},
                {"id_assessment": 2012, "type": "Exam", "due_date": 250,
                 "weight": 50, "score": None, "submitted_date": None, "is_banked": False},
            ],
            "vle_summary": {
                "total_clicks": 2110,
                "last_active_day": 45,
                "by_activity_type": {
                    "resource": 720, "oucontent": 640, "quiz": 410, "homepage": 340,
                },
                "weekly_clicks": [180, 220, 240, 210, 190, 160, 140, *([0] * 23)],
            },
        },
        # ── Lập trình Python — strong performance ────────────────────────────
        {
            "code_module": "COMP101",
            "code_presentation": "2024A",
            "title": "Lập trình Python",
            "module_length": 30,
            "registration_date": -15,
            "unregistration_date": None,
            "final_result": None,
            "assessments": [
                {"id_assessment": 3010, "type": "TMA", "due_date": 20,
                 "weight": 15, "score": 88, "submitted_date": 19, "is_banked": False},
                {"id_assessment": 3011, "type": "TMA", "due_date": 48,
                 "weight": 25, "score": 79, "submitted_date": 47, "is_banked": False},
                {"id_assessment": 3012, "type": "Exam", "due_date": 255,
                 "weight": 60, "score": None, "submitted_date": None, "is_banked": False},
            ],
            "vle_summary": {
                "total_clicks": 5240,
                "last_active_day": 46,
                "by_activity_type": {
                    "resource": 1480, "oucontent": 1620, "quiz": 1100,
                    "forumng": 540, "homepage": 500,
                },
                "weekly_clicks": [410, 460, 520, 480, 500, 470, 510, *([0] * 23)],
            },
        },
        # ── Xác suất & Thống kê Suy luận — on track ──────────────────────────
        {
            "code_module": "STAT110",
            "code_presentation": "2024A",
            "title": "Xác suất & Thống kê Suy luận",
            "module_length": 30,
            "registration_date": -15,
            "unregistration_date": None,
            "final_result": None,
            "assessments": [
                {"id_assessment": 4010, "type": "TMA", "due_date": 25,
                 "weight": 20, "score": 71, "submitted_date": 24, "is_banked": False},
                {"id_assessment": 4011, "type": "CMA", "due_date": 60,
                 "weight": 20, "score": None, "submitted_date": None, "is_banked": False},
                {"id_assessment": 4012, "type": "Exam", "due_date": 258,
                 "weight": 60, "score": None, "submitted_date": None, "is_banked": False},
            ],
            "vle_summary": {
                "total_clicks": 2980,
                "last_active_day": 44,
                "by_activity_type": {
                    "resource": 980, "oucontent": 870, "quiz": 620, "homepage": 510,
                },
                "weekly_clicks": [260, 300, 280, 310, 270, 240, 230, *([0] * 23)],
            },
        },
    ],
    # HIGH RISK — triggers O1 (> 0.7) and Wellbeing (> 0.8)
    "risk": {
        "tier": 3,
        "score": 0.82,
        "flags": ["low_vle_engagement", "assessment_due_soon", "assessment_shock"],
        "computed_at": datetime.utcnow().isoformat(),
    },
    "prerequisite_gaps": ["Thống kê cơ bản", "Đại số tuyến tính"],
    "updated_at": datetime.utcnow().isoformat(),
}

TIMETABLE = {
    "student_id": STUDENT_ID,
    "current_week": 7,
    "total_weeks": 30,
    "streak_days": 3,
    "lectures": [
        {"title": "Phân tích Dữ liệu & Thống kê", "subtitle": "Thứ 2, 08:00",
         "is_completed": False, "is_urgent": False},
        {"title": "Đại số Tuyến tính", "subtitle": "Thứ 4, 10:00",
         "is_completed": False, "is_urgent": False},
    ],
    "classes": [
        {"title": "Lab Lập trình Python", "subtitle": "Thứ 3, 13:00 · Phòng B204",
         "is_completed": False, "is_urgent": False},
        {"title": "Xác suất & Thống kê Suy luận", "subtitle": "Thứ 5, 09:00",
         "is_completed": False, "is_urgent": False},
    ],
    "assignments": [
        {"title": "TMA-02 — Phân tích hồi quy", "subtitle": "Nộp trước Thứ 6",
         "is_completed": False, "is_urgent": True},
    ],
    "exams": [],
}

STUDY_PLAN = {
    "student_id": STUDENT_ID,
    "sessions": [
        {"subject": "Ôn tập Tuần 6 — Phân tích Dữ liệu", "type": "review",
         "duration": 45, "day": "Thứ 2", "time": "19:00", "sm2_interval": 3},
        {"subject": "Luyện tập TMA-02", "type": "practice",
         "duration": 90, "day": "Thứ 4", "time": "19:30", "sm2_interval": None},
        {"subject": "Flashcard Thống kê cơ bản", "type": "spaced_rep",
         "duration": 20, "day": "Thứ 5", "time": "08:00", "sm2_interval": 7},
        {"subject": "Hoàn thiện TMA-02", "type": "assignment",
         "duration": 120, "day": "Thứ 6", "time": "14:00", "sm2_interval": None},
    ],
    "updated_at": datetime.utcnow().isoformat(),
}

KNOWLEDGE_STATES = {
    "student_id": STUDENT_ID,
    "states": {
        # All below 0.6 — visible as red/amber bars in Profile
        # Thống kê cơ bản + Đại số below 0.5 → skill gaps
        "Thống kê cơ bản":     {"mastery": 0.35, "last_updated": "2025-01-10", "evidence_count": 2},
        "Đại số tuyến tính":   {"mastery": 0.28, "last_updated": "2025-01-12", "evidence_count": 1},
        "Hồi quy tuyến tính":  {"mastery": 0.55, "last_updated": "2025-01-18", "evidence_count": 3},
        "Kiểm định giả thuyết":{"mastery": 0.42, "last_updated": "2025-01-20", "evidence_count": 2},
    },
    "updated_at": datetime.utcnow().isoformat(),
}

# TMA-02 due day 49. m2 due day 42 (past). m3 due day 45 (past). Both trigger milestone_check.
MILESTONES = {
    "student_id": STUDENT_ID,
    "id_assessment": 1753,
    "module": "DATA201",
    "title": "TMA-02 — Phân tích hồi quy",
    "milestones": [
        {"id": "m1", "title": "Đọc đề bài & tài liệu tham khảo",
         "status": "done", "due_offset_days": -14},    # due day 35 — done ✓
        {"id": "m2", "title": "Phân tích dữ liệu ban đầu",
         "status": "in_progress", "due_offset_days": -7},  # due day 42 < 46 — OVERDUE
        {"id": "m3", "title": "Viết báo cáo nháp",
         "status": "pending", "due_offset_days": -4},   # due day 45 < 46 — OVERDUE
        {"id": "m4", "title": "Nộp bài chính thức",
         "status": "pending", "due_offset_days": 0},    # due day 49 — not yet due
    ],
    "created_at": datetime.utcnow().isoformat(),
}

RISK_HISTORY = {
    "student_id": STUDENT_ID,
    "entries": [
        {"week": 1, "score": 0.30, "tier": 1},
        {"week": 2, "score": 0.38, "tier": 1},
        {"week": 3, "score": 0.46, "tier": 2},
        {"week": 4, "score": 0.55, "tier": 2},
        {"week": 5, "score": 0.66, "tier": 2},
        {"week": 6, "score": 0.74, "tier": 3},
        {"week": 7, "score": 0.82, "tier": 3},
    ],
    "updated_at": datetime.utcnow().isoformat(),
}

RESOURCES = [
    {
        "student_id": STUDENT_ID,
        "title": "Slide Tuần 7 — Kiểm định giả thuyết",
        "module": "DATA201",
        "type": "slide",
        "subject": "Kiểm định giả thuyết",
        "url": "https://example.com/bbb-w7-slides.pdf",
        "bookmarked": True,
        "created_at": datetime.utcnow().isoformat(),
    },
    {
        "student_id": STUDENT_ID,
        "title": "Hướng dẫn hồi quy tuyến tính với Python",
        "module": "DATA201",
        "type": "document",
        "subject": "Hồi quy tuyến tính",
        "url": "https://example.com/linear-regression.pdf",
        "bookmarked": False,
        "created_at": datetime.utcnow().isoformat(),
    },
    {
        "student_id": STUDENT_ID,
        "title": "Video: Thống kê cơ bản từ đầu",
        "module": "DATA201",
        "type": "video",
        "subject": "Thống kê cơ bản",
        "url": "https://example.com/stats-basics",
        "bookmarked": True,
        "created_at": datetime.utcnow().isoformat(),
    },
    {
        "student_id": STUDENT_ID,
        "title": "Quiz tự luyện — Đại số tuyến tính",
        "module": "DATA201",
        "type": "quiz",
        "subject": "Đại số tuyến tính",
        "url": "https://example.com/linear-algebra-quiz",
        "bookmarked": False,
        "created_at": datetime.utcnow().isoformat(),
    },
]


# ── Seed ───────────────────────────────────────────────────────────────────────

async def seed() -> None:
    if not MONGODB_URI or "placeholder" in MONGODB_URI:
        print("ERROR: MONGODB_URI not set or is placeholder. Check .env")
        sys.exit(1)

    client = AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=8000)
    try:
        await client.admin.command("ping")
        print(f"Connected to MongoDB — seeding {MONGODB_DB}")
    except Exception as e:
        print(f"ERROR: Cannot connect to MongoDB: {e}")
        sys.exit(1)

    db = client[MONGODB_DB]

    # Clear existing demo data for this student
    collections = [
        "students", "timetable_blocks", "study_plans",
        "knowledge_states", "assignment_milestones", "resources",
        "notifications", "risk_history",
    ]
    for col in collections:
        result = await db[col].delete_many({"student_id": STUDENT_ID})
        print(f"  Cleared {result.deleted_count:>3} docs from {col}")

    # Insert demo data
    await db.students.insert_one(STUDENT)
    print(f"  Inserted student {STUDENT_ID} (risk: {STUDENT['risk']['score']})")

    await db.timetable_blocks.insert_one(TIMETABLE)
    print("  Inserted timetable (week 7)")

    await db.study_plans.insert_one(STUDY_PLAN)
    print(f"  Inserted study plan ({len(STUDY_PLAN['sessions'])} sessions)")

    await db.knowledge_states.insert_one(KNOWLEDGE_STATES)
    n_states = len(KNOWLEDGE_STATES["states"])
    print(f"  Inserted knowledge states ({n_states} concepts)")

    await db.risk_history.insert_one(RISK_HISTORY)
    print(f"  Inserted risk history ({len(RISK_HISTORY['entries'])} weeks)")

    await db.assignment_milestones.insert_one(MILESTONES)
    overdue_count = sum(
        1 for m in MILESTONES["milestones"]
        if m["status"] not in ("done", "skipped")
        and (49 + m["due_offset_days"]) < CURRENT_DAY
    )
    print(f"  Inserted milestones ({overdue_count} overdue)")

    await db.resources.insert_many(RESOURCES)
    print(f"  Inserted {len(RESOURCES)} resources")

    print()
    print("Seed complete. Expected event_check triggers:")
    print("  1. deadline_warning    - TMA-02 due in 3 days (day 49, current day 46)")
    print("  2. assessment_shock    - TMA-01 score 42% -> O2 Course Planning")
    print("  3. vle_inactivity      - last active day 42 (4 days ago)")
    print("  4. milestone_check x2  - m2 (due day 42) + m3 (due day 45) both past due")
    print("  5. O1 risk_intervention- risk 0.82 > 0.7 -> O3 + Course Planner + Weekly Planner")
    print("  6. wellbeing           - risk 0.82 > 0.8")
    print()
    print("Trigger now:  POST http://localhost:8000/debug/trigger/event_check")
    print("Login with:   student_id=28400, any non-empty password")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
