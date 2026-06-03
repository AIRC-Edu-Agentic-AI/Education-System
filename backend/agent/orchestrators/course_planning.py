"""O2 — Course Planning Orchestrator.

Triggered by: enrollment, module midpoint, assessment shock, or called by O1.
Chains Student Skills gap check → Course Recommendation → Course Planning Agent.
"""
from datetime import datetime, timezone

from agent.student_skills import get_skill_gaps
from agent.course_recommendation import recommend_courses
from agent.course_planner import run_course_planning
from db.mongodb import get_db


async def run_course_planning_orchestration(student_id: int, trigger: str) -> None:
    print(f"[O2:course_planning] Starting for student {student_id} (trigger={trigger})")
    db = get_db()

    try:
        # Step 1 — Identify prerequisite gaps (Student Skills Agent)
        gaps = await get_skill_gaps(student_id, threshold=0.5)

        # Step 2 — Course recommendations based on current mastery
        recs = await recommend_courses(student_id)
        ready = recs.get("recommended", [])
        not_ready = recs.get("not_ready", [])

        # Step 3 — LLM course planner for detailed semester advice
        await run_course_planning(student_id, trigger=trigger)

        # Step 4 — Course guidance notification
        if ready:
            rec_titles = ", ".join(c["title"] for c in ready[:2])
            body = f"Dựa trên năng lực hiện tại, bạn có thể học: {rec_titles}."
        else:
            gap_str = ", ".join(gaps[:3]) if gaps else "một số khái niệm cơ bản"
            body = f"Cần củng cố thêm: {gap_str} trước khi chuyển sang môn tiếp theo."

        notif = {
            "student_id": student_id,
            "type": "course_guidance",
            "payload": {
                "title": "Gợi ý kế hoạch học kỳ",
                "body": body,
            },
            "action_options": [
                {"label": "Xem gợi ý khoá học", "action": "open_chat",
                 "payload": {"message": "Tôi nên học môn gì tiếp theo?"}},
            ],
            "read": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        from notify_schedule import compute_send_at
        send_at = compute_send_at("course_guidance")
        if send_at:
            notif["send_at"] = send_at
        if db is not None:
            await db.notifications.insert_one(notif)
        else:
            print(f"[O2] Course guidance: {notif['payload']['body']}")

        print(f"[O2:course_planning] Completed for student {student_id}")
    except Exception as e:
        print(f"[O2:course_planning] Error: {type(e).__name__}: {e}")
