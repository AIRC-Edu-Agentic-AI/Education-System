"""O1 — Risk Intervention Orchestrator.

Triggered when risk_score > 0.7. Chains O3 Performance Analysis →
Course Planning → Weekly Planning, then pushes a summary intervention.
"""
from agent.performance_analysis import run_performance_analysis
from agent.course_planner import run_course_planning
from agent.weekly_planner import run_weekly_planning
from db.mongodb import get_db
from db.notifications import push_notification


async def run_risk_intervention(student_id: int) -> None:
    print(f"[O1:risk_intervention] Starting for student {student_id}")
    db = get_db()

    try:
        # Step 1 — O3: analyse KT state, VLE, assessment scores
        perf = await run_performance_analysis(student_id)
        weak = perf.get("weak_concepts", [])

        # Step 2 — Course-level guidance (semester trajectory)
        await run_course_planning(student_id, trigger="orchestrated")

        # Step 3 — Rebuild weekly schedule to prioritise weak areas
        await run_weekly_planning(student_id, trigger="risk_spike")

        # Step 4 — High-priority summary notification
        weak_str = ", ".join(weak[:3]) if weak else "xem chi tiết trong ứng dụng"
        await push_notification(
            db, student_id, "risk_intervention",
            "Kế hoạch can thiệp học tập đã được cập nhật",
            f"Trợ lý đã phân tích và cập nhật kế hoạch của bạn. "
            f"Ưu tiên: {weak_str}. Kiểm tra lịch học và tư vấn mới trong ứng dụng.",
            action_options=[
                {"label": "Xem kế hoạch", "action": "open_chat",
                 "payload": {"message": "Cho tôi xem kế hoạch học tập mới"}},
            ],
        )

        print(f"[O1:risk_intervention] Completed for student {student_id}")
    except Exception as e:
        print(f"[O1:risk_intervention] Error: {type(e).__name__}: {e}")
