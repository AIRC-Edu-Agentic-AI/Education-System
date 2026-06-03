from datetime import datetime, timedelta

from db.mock_data import MOCK_STUDENT, MOCK_SCHEDULE, MOCK_MILESTONES
from db.mongodb import get_db

DEADLINE_WARN_DAYS = 3
VLE_INACTIVITY_DAYS = 3
WELLBEING_INACTIVITY_DAYS = 7
RISK_THRESHOLD = 0.7
RISK_WELLBEING_THRESHOLD = 0.8
ASSESSMENT_SHOCK_THRESHOLD = 50.0


async def run_event_check(student_id: int) -> None:
    db = get_db()

    if db is not None:
        doc = await db.students.find_one({"student_id": student_id})
        schedule_doc = await db.timetable_blocks.find_one({"student_id": student_id})
    else:
        doc = MOCK_STUDENT
        schedule_doc = MOCK_SCHEDULE

    if not doc:
        return

    current_day = _current_day(schedule_doc)
    risk = doc.get("risk", {})
    risk_score = risk.get("score", risk.get("risk_score", 0.0))

    # ── 1. Upcoming deadlines ──────────────────────────────────────────────────
    for enrollment in doc.get("enrollments", []):
        module = enrollment.get("title") or enrollment.get("code_module", "")
        for assessment in enrollment.get("assessments", []):
            if assessment.get("submitted_date"):
                continue
            due = assessment.get("due_date", 0)
            days_left = due - current_day
            if days_left < 0 or days_left > DEADLINE_WARN_DAYS:
                continue

            atype = assessment.get("type", "assignment")
            if days_left <= 1:
                notif_type = "deadline_critical"
                title = f"⚠️ {atype} — {module} hết hạn {'ngày mai' if days_left == 1 else 'hôm nay'}"
                body = f"Còn {days_left} ngày. Nộp bài ngay để tránh bị trừ điểm."
            else:
                notif_type = "deadline_warning"
                title = f"{atype} — {module} sắp đến hạn"
                body = f"Còn {days_left} ngày (đến ngày {due}). Hãy bắt đầu sớm."

            action_options = [
                {
                    "label": "Lên kế hoạch",
                    "action": "open_chat",
                    "payload": {"message": f"Giúp tôi lên kế hoạch hoàn thành {atype} môn {module}"},
                },
                {"label": "Nhắc lại sau", "action": "snooze", "payload": {}},
            ]
            await _push(db, student_id, notif_type, title, body, action_options)

    # ── 2. Assessment shock ────────────────────────────────────────────────────
    for enrollment in doc.get("enrollments", []):
        module = enrollment.get("title") or enrollment.get("code_module", "")
        for assessment in enrollment.get("assessments", []):
            score = assessment.get("score")
            atype = assessment.get("type", "")
            if atype == "Exam":
                continue  # only check formative assessments
            if score is not None and score < ASSESSMENT_SHOCK_THRESHOLD:
                action_options = [
                    {
                        "label": "Nhận tư vấn kế hoạch",
                        "action": "open_chat",
                        "payload": {"message": f"Tôi bị điểm thấp trong {atype} môn {module}, cần kế hoạch cải thiện"},
                    },
                ]
                is_new = await _push(
                    db, student_id, "assessment_shock",
                    f"Điểm {atype} — {module} thấp ({score:.0f}%)",
                    "Điểm dưới 50%. Trợ lý có thể giúp bạn lên kế hoạch cải thiện.",
                    action_options,
                )
                # Only run the expensive O2 orchestration when this is a NEW shock
                # (not seen in the last 24h) — avoids re-planning on every tick.
                if is_new:
                    from agent.orchestrators.course_planning import run_course_planning_orchestration
                    await run_course_planning_orchestration(student_id, trigger="assessment_shock")

    # ── 3. VLE inactivity ──────────────────────────────────────────────────────
    vle = doc.get("enrollments", [{}])[0].get("vle_summary", {})
    last_active = vle.get("last_active_day", current_day)
    days_inactive = 0
    if last_active < current_day:
        days_inactive = current_day - last_active
        if days_inactive > VLE_INACTIVITY_DAYS:
            title = "Bạn chưa học trong một thời gian"
            body = f"Không có hoạt động trong {days_inactive} ngày. Quay lại học ngay hôm nay!"
            action_options = [
                {
                    "label": "Hỏi trợ lý",
                    "action": "open_chat",
                    "payload": {"message": "Hôm nay tôi nên học gì?"},
                },
            ]
            await _push(db, student_id, "vle_inactivity", title, body, action_options)
        # Wellbeing trigger: severe inactivity (deduped — once per 24h)
        if days_inactive > WELLBEING_INACTIVITY_DAYS:
            if not await _recently_fired(db, student_id, "wellbeing"):
                from agent.wellbeing import run_wellbeing_check
                await run_wellbeing_check(student_id, trigger="inactivity")

    # ── 4. Milestone overdue check ─────────────────────────────────────────────
    milestone_docs = []
    if db is not None:
        cursor = db.assignment_milestones.find({"student_id": student_id})
        milestone_docs = await cursor.to_list(length=20)
    else:
        milestone_docs = [m for m in MOCK_MILESTONES if m["student_id"] == student_id]

    # Build due_date lookup from assessments
    due_dates: dict[int, int] = {}
    for enrollment in doc.get("enrollments", []):
        for a in enrollment.get("assessments", []):
            due_dates[a["id_assessment"]] = a.get("due_date", 9999)

    for ms_doc in milestone_docs:
        id_assessment = ms_doc.get("id_assessment", 0)
        assignment_due = due_dates.get(id_assessment, 9999)
        for ms in ms_doc.get("milestones", []):
            if ms.get("status") in ("done", "skipped"):
                continue
            ms_due = assignment_due + ms.get("due_offset_days", 0)
            if ms_due < current_day:
                action_options = [
                    {"label": "Đánh dấu xong", "action": "update_milestone",
                     "payload": {"id_assessment": id_assessment, "milestone_id": ms["id"], "status": "done"}},
                    {"label": "Bỏ qua", "action": "update_milestone",
                     "payload": {"id_assessment": id_assessment, "milestone_id": ms["id"], "status": "skipped"}},
                    {"label": "Hỏi trợ lý", "action": "open_chat",
                     "payload": {"message": f"Giúp tôi hoàn thành: {ms['title']}"}},
                ]
                await _push(
                    db, student_id, "milestone_check",
                    f"Cột mốc quá hạn: {ms['title']}",
                    f"Cột mốc này đã quá hạn {current_day - ms_due} ngày.",
                    action_options,
                )

    # ── 5. High risk → O1 Risk Intervention Orchestrator ──────────────────────
    if risk_score > RISK_THRESHOLD:
        # Wellbeing check for severe risk (deduped — once per 24h)
        if risk_score > RISK_WELLBEING_THRESHOLD:
            if not await _recently_fired(db, student_id, "wellbeing"):
                from agent.wellbeing import run_wellbeing_check
                await run_wellbeing_check(student_id, trigger="risk")

        # O1: full intervention chain (Performance Analysis → Course Planning → Weekly Planning).
        # Gated to once per 24h — re-running on every tick with unchanged risk
        # would needlessly rebuild the study plan and burn tokens.
        if not await _recently_fired(db, student_id, "risk_intervention"):
            from agent.orchestrators.risk_intervention import run_risk_intervention
            await run_risk_intervention(student_id)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _current_day(schedule_doc: dict | None) -> int:
    """Approximate current module day from week number (mid-week)."""
    week = (schedule_doc or {}).get("current_week", 7)
    return week * 7 - 3


async def _recently_fired(db, student_id: int, notif_type: str, hours: int = 24) -> bool:
    """True if a notification of this type was created within the window.

    Used to gate expensive agent runs (O1, Wellbeing) that produce a
    notification of `notif_type` — prevents re-running them every tick
    when the underlying state (e.g. risk_score) is unchanged.
    """
    if db is None:
        return False
    cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    existing = await db.notifications.find_one({
        "student_id": student_id,
        "type": notif_type,
        "created_at": {"$gt": cutoff},
    })
    return existing is not None


async def _push(
    db,
    student_id: int,
    notif_type: str,
    title: str,
    body: str,
    action_options: list,
) -> bool:
    """Insert a notification, deduped within a 24h window per type.

    Returns True if a new notification was inserted, False if it was
    suppressed as a duplicate. Callers use this to gate expensive
    follow-up agent runs so they only fire when something is genuinely new.
    """
    notif = {
        "student_id": student_id,
        "type": notif_type,
        "payload": {"title": title, "body": body},
        "action_options": action_options,
        "read": False,
        "created_at": datetime.utcnow().isoformat(),
    }
    if db is not None:
        cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()
        existing = await db.notifications.find_one({
            "student_id": student_id,
            "type": notif_type,
            "created_at": {"$gt": cutoff},
        })
        if existing:
            return False
        await db.notifications.insert_one(notif)
        return True
    else:
        print(f"[event_checker] {notif_type} — {title}")
        return True
