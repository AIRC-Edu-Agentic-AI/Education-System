import asyncio

from db.mock_data import MOCK_STUDENT, MOCK_SCHEDULE, MOCK_MILESTONES
from db.mongodb import get_db
from db.notifications import push_notification, recently_fired

DEADLINE_WARN_DAYS = 3
VLE_INACTIVITY_DAYS = 3
WELLBEING_INACTIVITY_DAYS = 7
RISK_THRESHOLD = 0.7
RISK_WELLBEING_THRESHOLD = 0.8
ASSESSMENT_SHOCK_THRESHOLD = 50.0
# Progress check-in: nudge for assignments due beyond the urgent deadline window
# but within this horizon; flag "behind" when close and not yet started.
PROGRESS_HORIZON_DAYS = 14
PROGRESS_BEHIND_DAYS = 7


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

    # LLM follow-ups are deferred and run in parallel *after* all the fast,
    # deterministic notification pushes below — so instant notifications never
    # wait behind multi-minute agent chains. The LLM pool bounds real concurrency.
    followups: list = []
    wellbeing_queued = False

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
                # Queue the expensive O2 orchestration only for a NEW shock
                # (not seen in the last 24h) — avoids re-planning on every tick.
                if is_new:
                    from agent.orchestrators.course_planning import run_course_planning_orchestration
                    followups.append(
                        run_course_planning_orchestration(student_id, trigger="assessment_shock"))

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
        if days_inactive > WELLBEING_INACTIVITY_DAYS and not wellbeing_queued:
            if not await _recently_fired(db, student_id, "wellbeing"):
                from agent.wellbeing import run_wellbeing_check
                followups.append(run_wellbeing_check(student_id, trigger="inactivity"))
                wellbeing_queued = True

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
        if risk_score > RISK_WELLBEING_THRESHOLD and not wellbeing_queued:
            if not await _recently_fired(db, student_id, "wellbeing"):
                from agent.wellbeing import run_wellbeing_check
                followups.append(run_wellbeing_check(student_id, trigger="risk"))
                wellbeing_queued = True

        # O1: full intervention chain (Performance Analysis → Course Planning → Weekly Planning).
        # Gated to once per 24h — re-running on every tick with unchanged risk
        # would needlessly rebuild the study plan and burn tokens.
        if not await _recently_fired(db, student_id, "risk_intervention"):
            from agent.orchestrators.risk_intervention import run_risk_intervention
            followups.append(run_risk_intervention(student_id))

    # ── Run all deferred LLM follow-ups in parallel ───────────────────────────
    # Deterministic notifications above are already persisted. These agent
    # chains fan out across the LLM pool; with one endpoint they queue.
    if followups:
        await asyncio.gather(*followups, return_exceptions=True)


# ── Proactive progress check-in ─────────────────────────────────────────────────

def _status_chips(id_assessment, milestone_id) -> list:
    """Three self-report chips for one milestone. Each sets the milestone tracker
    to the chosen status — a one-tap answer to the progress question."""
    def mk(label: str, status: str) -> dict:
        return {"label": label, "action": "update_milestone",
                "payload": {"id_assessment": id_assessment,
                            "milestone_id": milestone_id, "status": status}}
    return [
        mk("Chưa bắt đầu", "pending"),
        mk("Đang làm", "in_progress"),
        mk("Đã xong", "done"),
    ]


async def run_progress_check(student_id: int) -> None:
    """Gentle, early check-in on in-flight assignments — fires BEFORE anything is
    overdue. For each unsubmitted assessment due beyond the urgent deadline window
    (>3 days) but within PROGRESS_HORIZON_DAYS, it nudges with current milestone
    progress. If the student is close (<= PROGRESS_BEHIND_DAYS) and hasn't started,
    it flags "behind" and triggers a replan."""
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

    # Milestone progress lookup by assessment id
    if db is not None:
        cursor = db.assignment_milestones.find({"student_id": student_id})
        ms_docs = await cursor.to_list(length=50)
    else:
        ms_docs = [m for m in MOCK_MILESTONES if m["student_id"] == student_id]
    ms_by_assessment = {m.get("id_assessment"): m.get("milestones", []) for m in ms_docs}

    # Collect candidate nudges, then emit ONE prioritised check-in (behind wins,
    # else soonest deadline). Avoids flooding / type-dedup collapsing the wrong one.
    candidates: list[tuple] = []   # (priority, days_left, title, body, action_options)
    behind = False
    for enrollment in doc.get("enrollments", []):
        module = enrollment.get("title") or enrollment.get("code_module", "")
        for a in enrollment.get("assessments", []):
            if a.get("submitted_date"):
                continue
            days_left = a.get("due_date", 0) - current_day
            if days_left <= DEADLINE_WARN_DAYS or days_left > PROGRESS_HORIZON_DAYS:
                continue  # urgent window owned by deadline check; far ones skipped

            atype = a.get("type", "assignment")
            aid = a.get("id_assessment")
            mss = ms_by_assessment.get(aid, [])
            total = len(mss)
            done = sum(1 for m in mss if m.get("status") == "done")
            started = any(m.get("status") in ("done", "in_progress") for m in mss)
            # The milestone we check in about: the active one, else the next pending.
            target = (next((m for m in mss if m.get("status") == "in_progress"), None)
                      or next((m for m in mss if m.get("status") == "pending"), None))

            is_behind = days_left <= PROGRESS_BEHIND_DAYS and not started
            if is_behind:
                behind = True
            title = f"Tiến độ {atype} — {module}" + (": cần tăng tốc" if is_behind else "")

            if target:
                # Phrase it as a question about a specific milestone; chips answer it.
                mtitle = target.get("title", "")
                body = (f"Bạn đã làm đến đâu với “{mtitle}” (môn {module})? "
                        f"Còn {days_left} ngày · {done}/{total} cột mốc đã xong.")
                action_options = _status_chips(aid, target.get("id"))
            elif total:  # every milestone done/skipped
                body = (f"Còn {days_left} ngày · tất cả {total} cột mốc đã xong. "
                        "Sẵn sàng nộp bài chưa?")
                action_options = [{"label": "Hỏi trợ lý", "action": "open_chat",
                                   "payload": {"message": f"Tôi đã hoàn thành các bước cho {atype} môn {module}"}}]
            else:  # not broken down yet — planning needs a conversation
                body = (f"Còn {days_left} ngày. Bạn đã lên kế hoạch chi tiết cho "
                        f"{atype} môn {module} chưa?")
                action_options = [{"label": "Lên kế hoạch chi tiết", "action": "open_chat",
                                   "payload": {"message": f"Giúp tôi chia nhỏ {atype} môn {module} thành các bước"}}]

            candidates.append((0 if is_behind else 1, days_left, title, body, action_options))

    if candidates:
        candidates.sort(key=lambda c: (c[0], c[1]))  # behind first, then soonest deadline
        _, _, title, body, action_options = candidates[0]
        await _push(db, student_id, "progress_check", title, body, action_options)

    # Behind schedule → replan (the only condition under which a check-in replans)
    if behind:
        from agent.weekly_planner import run_weekly_planning
        await run_weekly_planning(student_id, trigger="behind_schedule")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _current_day(schedule_doc: dict | None) -> int:
    """Approximate current module day from week number (mid-week)."""
    week = (schedule_doc or {}).get("current_week", 7)
    return week * 7 - 3


async def _recently_fired(db, student_id: int, notif_type: str, hours: int = 24) -> bool:
    """Gate for expensive agent runs (O1, Wellbeing) keyed on their notif type."""
    return await recently_fired(db, student_id, notif_type, hours)


async def _push(
    db,
    student_id: int,
    notif_type: str,
    title: str,
    body: str,
    action_options: list,
) -> bool:
    """Insert a deterministic notification, deduped 24h per type. Returns True
    if inserted, False if suppressed — callers gate follow-ups on the result."""
    return await push_notification(
        db, student_id, notif_type, title, body,
        action_options=action_options, dedup_hours=24)
