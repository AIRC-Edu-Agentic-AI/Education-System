"""Dev/admin router — powers the browser dashboard.

Exposes an agent registry, a manual trigger endpoint (scheduler jobs +
individual agents/orchestrators), and an in-memory run log the dashboard polls
to show agent activity. Dev-only: no auth, relies on open CORS.
"""
import asyncio
import itertools
from collections import deque
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.mock_data import MOCK_STUDENT

router = APIRouter()

DEFAULT_SID = MOCK_STUDENT["student_id"]

# Scheduler job ids (triggered by poking next_run_time)
SCHEDULER_JOBS = ["event_check", "daily_plan", "weekly_plan", "progress_report", "progress_check"]

# Human-readable cadence per job (for the dashboard's Scheduler panel)
SCHEDULE_LABELS = {
    "event_check": "Every 15 min",
    "daily_plan": "Daily · 08:00",
    "weekly_plan": "Mon · 08:05",
    "progress_report": "Sun · 20:00",
    "progress_check": "Daily · 12:00",
}

# ── In-memory run log ───────────────────────────────────────────────────────────

RUN_LOG: deque = deque(maxlen=50)
_run_counter = itertools.count(1)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _run_logged(run_id: int, target: str, coro) -> None:
    entry = next((e for e in RUN_LOG if e["id"] == run_id), None)
    try:
        await coro
        if entry:
            entry["status"] = "completed"
    except Exception as e:  # noqa: BLE001 — surface any agent failure to the UI
        if entry:
            entry["status"] = "error"
            entry["detail"] = f"{type(e).__name__}: {e}"
        print(f"[admin] {target} error: {type(e).__name__}: {e}")
    finally:
        if entry:
            entry["ended_at"] = _now()


def _record(target: str, status: str = "started", detail: str = "") -> int:
    run_id = next(_run_counter)
    RUN_LOG.appendleft({
        "id": run_id,
        "target": target,
        "status": status,
        "detail": detail,
        "started_at": _now(),
        "ended_at": _now() if status != "started" else None,
    })
    return run_id


# ── Agent registry ───────────────────────────────────────────────────────────────
# target -> {label, description, params, factory(sid, trigger, id_assessment) -> coro}

def _agent_registry() -> dict:
    from agent.performance_analysis import run_performance_analysis
    from agent.orchestrators.risk_intervention import run_risk_intervention
    from agent.orchestrators.course_planning import run_course_planning_orchestration
    from agent.wellbeing import run_wellbeing_check
    from agent.assignment_breakdown import run_breakdown
    from agent.course_planner import run_course_planning

    return {
        "risk_intervention": {
            "label": "O1 · Risk Intervention",
            "description": "Performance Analysis → Course Planning → Weekly Planning, then a summary notification.",
            "params": [],
            "factory": lambda sid, trigger, idass: run_risk_intervention(sid),
        },
        "course_planning": {
            "label": "O2 · Course Planning",
            "description": "Skill gaps → Course Recommendation → Course Planner → guidance notification.",
            "params": ["trigger"],
            "factory": lambda sid, trigger, idass: run_course_planning_orchestration(
                sid, trigger or "orchestrated"),
        },
        "performance_analysis": {
            "label": "O3 · Performance Analysis",
            "description": "Synthesise KT state, VLE, and scores into a performance snapshot.",
            "params": [],
            "factory": lambda sid, trigger, idass: run_performance_analysis(sid),
        },
        "wellbeing": {
            "label": "Wellbeing Agent",
            "description": "Empathetic notification + schedule relief (weekly replan).",
            "params": ["trigger"],
            "factory": lambda sid, trigger, idass: run_wellbeing_check(sid, trigger or "risk"),
        },
        "assignment_breakdown": {
            "label": "Assignment Breakdown",
            "description": "Generate milestones for an assessment (default TMA-02, id 1753).",
            "params": ["id_assessment"],
            "factory": lambda sid, trigger, idass: run_breakdown(sid, idass or 1753),
        },
        "course_planner": {
            "label": "Course Planner (specialist)",
            "description": "Semester-level trajectory advice for one student.",
            "params": ["trigger"],
            "factory": lambda sid, trigger, idass: run_course_planning(
                sid, trigger or "midpoint"),
        },
    }


# ── Models ───────────────────────────────────────────────────────────────────────

class TriggerRequest(BaseModel):
    target: str
    student_id: int | None = None
    trigger: str | None = None
    id_assessment: int | None = None


class ScoreEvent(BaseModel):
    student_id: int | None = None
    id_assessment: int
    score: float


class AssignmentEvent(BaseModel):
    student_id: int | None = None
    module_code: str
    type: str = "TMA"
    due_date: int
    weight: float = 10
    title: str | None = None


# ── Endpoints ──────────────────────────────────────────────────────────────────────

@router.get("/agents")
async def list_agents():
    from scheduler import scheduler
    jobs = []
    for jid in SCHEDULER_JOBS:
        job = scheduler.get_job(jid)
        jobs.append({
            "id": jid,
            "schedule": SCHEDULE_LABELS.get(jid, str(job.trigger) if job else ""),
            "next_run_time": job.next_run_time.isoformat()
            if job and job.next_run_time else None,
        })
    agents = [
        {"target": k, "label": v["label"], "description": v["description"], "params": v["params"]}
        for k, v in _agent_registry().items()
    ]
    return {"jobs": jobs, "agents": agents, "default_student_id": DEFAULT_SID}


@router.post("/trigger")
async def trigger(req: TriggerRequest):
    sid = req.student_id or DEFAULT_SID

    # Scheduler job → poke next_run_time to now
    if req.target in SCHEDULER_JOBS:
        from scheduler import scheduler
        job = scheduler.get_job(req.target)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job '{req.target}' not found")
        job.modify(next_run_time=datetime.now())
        run_id = _record(req.target, status="started", detail="scheduler job poked")
        # Scheduler runs it imminently; mark dispatched
        entry = RUN_LOG[0]
        entry["status"] = "dispatched"
        entry["ended_at"] = _now()
        return {"started": req.target, "run_id": run_id}

    # Registered agent → run in background, logged
    registry = _agent_registry()
    spec = registry.get(req.target)
    if not spec:
        raise HTTPException(status_code=404, detail=f"Unknown target '{req.target}'")

    coro = spec["factory"](sid, req.trigger, req.id_assessment)
    run_id = _record(req.target, status="started",
                     detail=f"student {sid}"
                            + (f", trigger={req.trigger}" if req.trigger else "")
                            + (f", id_assessment={req.id_assessment}" if req.id_assessment else ""))
    asyncio.create_task(_run_logged(run_id, req.target, coro))
    return {"started": req.target, "run_id": run_id, "student_id": sid}


@router.get("/runs")
async def runs():
    return list(RUN_LOG)


class SettingsRequest(BaseModel):
    schedule_enabled: bool | None = None
    spread_minutes: int | None = None


@router.get("/notification-plan")
async def notification_plan(student_id: int | None = None):
    """Notifications scheduled for later (send_at in the future) — the queue the
    dispatcher will release. Sorted by send time."""
    from db.mongodb import get_db
    db = get_db()
    sid = student_id or DEFAULT_SID
    if db is None:
        return []
    now_iso = datetime.now(timezone.utc).isoformat()
    cur = db.notifications.find(
        {"student_id": sid, "send_at": {"$gt": now_iso}}).sort("send_at", 1).limit(30)
    docs = await cur.to_list(length=30)
    return [{
        "type": d.get("type"),
        "title": (d.get("payload") or {}).get("title", ""),
        "send_at": d.get("send_at"),
    } for d in docs]


@router.get("/settings")
async def get_settings():
    import notify_schedule
    return notify_schedule.get_settings()


@router.post("/settings")
async def set_settings(req: SettingsRequest):
    import notify_schedule
    result = notify_schedule.set_settings(
        enabled=req.schedule_enabled, spread_minutes=req.spread_minutes)
    await notify_schedule.save_settings_db()  # persist across restarts
    return result


@router.post("/demo/run")
async def demo_run():
    """One-click idempotent demo: reset the demo student to the known at-risk
    state (also clears the 24h agent dedup), then fire the event_check cascade.
    The dashboard's pollers surface the notifications and agent runs that follow.
    """
    from db.mongodb import get_db
    from db.seed import seed_demo

    db = get_db()
    if db is None:
        raise HTTPException(
            status_code=503,
            detail="Demo requires a live database (set USE_MOCK_DATA=false and connect MongoDB).",
        )

    # Keep the demo instant even if notification scheduling is enabled.
    import notify_schedule
    notify_schedule.force_immediate(180)

    summary = await seed_demo(db)
    _record("demo_reset", status="completed",
            detail=f"reset student {summary['student_id']} (risk {summary['risk_score']})")

    # Fire the full agentic cascade via the scheduler's event_check job.
    from scheduler import scheduler
    job = scheduler.get_job("event_check")
    if job:
        job.modify(next_run_time=datetime.now())
        _record("event_check", status="dispatched", detail="demo cascade")

    return {"ok": True, "summary": summary}


# ── Inbound data events (emitted from the dashboard) ───────────────────────────
# Approx "today" in module-day terms (matches the seed's week-7 assumption).
_CURRENT_DAY = 46


def _find_assessment(doc: dict, id_assessment: int):
    """Return (enrollment, assessment) for an assessment id, or (None, None)."""
    for e in doc.get("enrollments", []):
        for a in e.get("assessments", []):
            if a.get("id_assessment") == id_assessment:
                return e, a
    return None, None


async def _react(student_id: int, summary: str) -> None:
    from agent.assessment_reaction import react_to_assessment_change
    run_id = _record("assessment_reaction", status="started", detail=summary)
    asyncio.create_task(
        _run_logged(run_id, "assessment_reaction",
                    react_to_assessment_change(student_id, summary, replan=True)))


@router.post("/event/score")
async def event_score(ev: ScoreEvent):
    """A new score was received for an existing assessment → record it,
    notify the student with a recommended next action, and replan."""
    from db.mongodb import get_db
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Requires a live database.")
    sid = ev.student_id or DEFAULT_SID

    doc = await db.students.find_one({"student_id": sid})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Student {sid} not found")
    enrollment, assessment = _find_assessment(doc, ev.id_assessment)
    if not assessment:
        raise HTTPException(status_code=404, detail=f"Assessment {ev.id_assessment} not found")

    await db.students.update_one(
        {"student_id": sid},
        {"$set": {
            "enrollments.$[e].assessments.$[a].score": ev.score,
            "enrollments.$[e].assessments.$[a].submitted_date": _CURRENT_DAY,
        }},
        array_filters=[
            {"e.code_module": {"$exists": True}},
            {"a.id_assessment": ev.id_assessment},
        ],
    )

    module = enrollment.get("title") or enrollment.get("code_module", "")
    summary = f"Điểm mới: {assessment.get('type', '')} — {module}: {ev.score:.0f}%"
    await _react(sid, summary)
    return {"ok": True, "summary": summary, "student_id": sid}


@router.post("/event/assignment")
async def event_assignment(ev: AssignmentEvent):
    """A new assignment was received → add it, notify with a starting step, replan."""
    from db.mongodb import get_db
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Requires a live database.")
    sid = ev.student_id or DEFAULT_SID

    doc = await db.students.find_one({"student_id": sid})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Student {sid} not found")

    target_enr = next(
        (e for e in doc.get("enrollments", []) if e.get("code_module") == ev.module_code),
        None,
    )
    if not target_enr:
        raise HTTPException(status_code=404, detail=f"Module {ev.module_code} not found")

    all_ids = [a.get("id_assessment", 0)
               for e in doc.get("enrollments", []) for a in e.get("assessments", [])]
    new_id = (max(all_ids) if all_ids else 1000) + 1
    new_assessment = {
        "id_assessment": new_id,
        "type": ev.type,
        "due_date": ev.due_date,
        "weight": ev.weight,
        "score": None,
        "submitted_date": None,
        "is_banked": False,
    }
    await db.students.update_one(
        {"student_id": sid},
        {"$push": {"enrollments.$[e].assessments": new_assessment}},
        array_filters=[{"e.code_module": ev.module_code}],
    )

    module = target_enr.get("title") or ev.module_code
    summary = (f"Bài tập mới: {ev.type} — {module} "
               f"(hạn ngày {ev.due_date}, {ev.weight:.0f}%)")
    await _react(sid, summary)
    return {"ok": True, "summary": summary, "id_assessment": new_id, "student_id": sid}
