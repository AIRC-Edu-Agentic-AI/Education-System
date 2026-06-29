"""Wellbeing Agent.

Triggered when: risk_score > 0.8 OR VLE inactivity > 7 days OR stress keywords detected in chat.
Creates an empathetic notification and optionally triggers schedule relief.
"""
from db.mongodb import get_db
from db.notifications import push_notification

WELLBEING_RELIEF_TRIGGER = "wellbeing_relief"

# Lightweight stress keyword detection (no ML)
_STRESS_KEYWORDS_EN = {
    "stressed", "overwhelmed", "can't", "struggling", "hard", "difficult",
    "behind", "lost", "exhausted", "worried", "anxious", "confused",
}
_STRESS_KEYWORDS_VI = {
    "căng thẳng", "mệt", "khó quá", "không theo kịp", "chán", "lo lắng",
    "không hiểu", "bị lạc", "quá sức", "áp lực",
}


def has_stress_signal(messages: list[dict]) -> bool:
    """Detect stress keywords in the last 3 user messages."""
    recent_text = " ".join(
        m.get("content", "") for m in messages[-3:]
        if m.get("role") == "user"
    ).lower()
    all_keywords = _STRESS_KEYWORDS_EN | _STRESS_KEYWORDS_VI
    return any(kw in recent_text for kw in all_keywords)


async def run_wellbeing_check(student_id: int, trigger: str = "risk") -> None:
    db = get_db()

    trigger_messages = {
        "risk": "Điểm rủi ro học tập của bạn đang ở mức cao.",
        "inactivity": "Bạn đã không hoạt động trong VLE một thời gian dài.",
        "stress": "Trợ lý nhận thấy bạn đang gặp khó khăn.",
    }
    reason = trigger_messages.get(trigger, "")

    await push_notification(
        db, student_id, "wellbeing",
        "Trợ lý quan tâm đến bạn",
        f"{reason} Học tập có thể căng thẳng — nhưng bạn không cần đối mặt một mình. "
        "Trợ lý đã điều chỉnh lịch học để giảm tải cho bạn.",
        action_options=[
            {"label": "Nói chuyện với trợ lý", "action": "open_chat",
             "payload": {"message": "Tôi đang cảm thấy rất áp lực, hãy giúp tôi"}},
            {"label": "Xem lịch học mới", "action": "open_chat",
             "payload": {"message": "Cho tôi xem lịch học đã được điều chỉnh"}},
        ],
    )

    # Schedule relief: trigger weekly planner to lighten the load
    try:
        from agent.weekly_planner import run_weekly_planning
        await run_weekly_planning(student_id, trigger=WELLBEING_RELIEF_TRIGGER)
    except Exception as e:
        print(f"[wellbeing] Relief planning failed: {e}")
