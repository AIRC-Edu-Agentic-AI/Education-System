import json
from datetime import datetime, timezone
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool

from db.mock_data import MOCK_STUDENT, MOCK_SCHEDULE, MOCK_STUDY_PLAN, MOCK_KNOWLEDGE_STATES, MOCK_RESOURCES, MOCK_MILESTONES, MOCK_NEXT_COURSES
from db.mongodb import get_db

# ── Think-tag helpers (shared with chat router) ───────────────────────────────

_THINK_OPEN = "<think>"
_THINK_CLOSE = "</think>"


def _partial_tag(s: str, tag: str) -> int:
    """Length of longest suffix of s that is a prefix of tag (safe buffering)."""
    for n in range(min(len(tag) - 1, len(s)), 0, -1):
        if s.endswith(tag[:n]):
            return n
    return 0


# ── Write-tool metadata ───────────────────────────────────────────────────────

WRITE_TOOL_NAMES = {
    "update_study_plan",
    "create_reminder",
    "mark_assignment_complete",
    "save_study_note",
    "update_knowledge_state",
    "break_down_assignment",
    "update_milestone_status",
}

WRITE_TOOL_RESOURCES: dict[str, list[str]] = {
    "update_study_plan": ["study_plan"],
    "create_reminder": ["notifications"],
    "mark_assignment_complete": ["assignments"],
    "save_study_note": ["resources"],
    "update_knowledge_state": ["knowledge_state"],
    "break_down_assignment": ["assignments", "milestones"],
    "update_milestone_status": ["milestones"],
}


# ── Bayesian Knowledge Tracing update rule ────────────────────────────────────

_EVIDENCE_WEIGHTS = {
    "quiz": 0.3,
    "assignment": 0.4,
    "self_report": 0.1,
    "tutor_interaction": 0.2,
}


def update_mastery(current: float, evidence_type: str, score: float) -> float:
    """Weighted exponential moving average update toward observed score."""
    w = _EVIDENCE_WEIGHTS.get(evidence_type, 0.15)
    return round(max(0.0, min(1.0, current + w * (score - current))), 4)


# ── Student context snapshot ──────────────────────────────────────────────────

def _extract_context(doc: dict) -> dict:
    enrollment = doc.get("enrollments", [{}])[0]
    assessments = enrollment.get("assessments", [])
    unsubmitted = [a for a in assessments if not a.get("submitted_date")]
    risk = doc.get("risk", {})
    return {
        "full_name": doc.get("full_name", "Student"),
        "risk_tier": risk.get("tier", risk.get("risk_tier", 1)),
        "risk_score": risk.get("score", risk.get("risk_score", 0.0)),
        "risk_flags": risk.get("flags", risk.get("risk_flags", [])),
        "module": enrollment.get("title") or enrollment.get("code_module", ""),
        "enrolled_courses": [
            e.get("title") or e.get("code_module", "")
            for e in doc.get("enrollments", [])
        ],
        "unsubmitted_count": len(unsubmitted),
        "next_due": min((a["due_date"] for a in unsubmitted), default=None),
        "prerequisite_gaps": doc.get("prerequisite_gaps", []),
    }


async def _get_student_doc(student_id: int) -> dict:
    db = get_db()
    if db is not None:
        doc = await db.students.find_one({"student_id": student_id})
        if doc:
            return doc
    return MOCK_STUDENT


async def get_student_context(student_id: int) -> dict:
    db = get_db()
    if db is not None:
        doc = await db.students.find_one({"student_id": student_id})
        if doc:
            return _extract_context(doc)
    return _extract_context(MOCK_STUDENT)


async def get_knowledge_state_stub(student_id: int) -> dict:
    """Return per-concept mastery probabilities from knowledge_states collection (or mock)."""
    db = get_db()
    if db is not None:
        doc = await db.knowledge_states.find_one({"student_id": student_id})
        if doc:
            return {k: v["mastery"] for k, v in doc.get("states", {}).items()}
    states = MOCK_KNOWLEDGE_STATES.get("states", {})
    return {k: v["mastery"] for k, v in states.items()}


# ── Tutoring intent detection ─────────────────────────────────────────────────

_TUTORING_KEYWORDS_EN = {
    "explain", "what is", "what are", "how does", "how do", "how is",
    "why does", "why is", "why are", "difference between", "compare",
    "example", "define", "definition", "solve", "calculate", "prove",
    "describe", "concept", "formula", "theorem", "algorithm",
}
_TUTORING_KEYWORDS_VI = {
    "giải thích", "là gì", "là cái gì", "như thế nào", "tại sao",
    "khác nhau", "so sánh", "ví dụ", "định nghĩa", "giải", "tính",
    "chứng minh", "mô tả", "khái niệm", "công thức", "định lý",
    "thuật toán", "cách tính", "cách làm",
}

_PERFORMANCE_KEYWORDS_EN = {
    "how am i doing", "how am i performing", "performance", "progress report",
    "my results", "how have i", "show my scores", "overview of my",
}
_PERFORMANCE_KEYWORDS_VI = {
    "kết quả", "hiệu suất", "tiến độ", "tình hình học",
    "tôi đang làm tốt", "báo cáo học tập", "xem kết quả",
}

_RECOMMENDATION_KEYWORDS_EN = {
    "recommend", "next course", "what should i study", "what course",
    "which module", "suggest a course", "course recommendation",
}
_RECOMMENDATION_KEYWORDS_VI = {
    "gợi ý khoá học", "học môn gì tiếp theo", "nên học gì", "khoá học tiếp theo",
    "môn học tiếp", "đề xuất môn học",
}

_WELLBEING_KEYWORDS_EN = {
    "stressed", "overwhelmed", "can't cope", "struggling", "exhausted",
    "burned out", "anxious", "worried", "confused", "lost", "behind",
}
_WELLBEING_KEYWORDS_VI = {
    "căng thẳng", "mệt mỏi", "quá tải", "không theo kịp", "lo lắng",
    "áp lực", "chán nản", "không hiểu gì", "bị lạc", "khó quá",
}


def _detect_intent(text: str) -> str:
    """Classify message intent: tutoring | performance | recommendation | wellbeing | general."""
    lower = text.lower()
    if any(kw in lower for kw in _WELLBEING_KEYWORDS_EN | _WELLBEING_KEYWORDS_VI):
        return "wellbeing"
    if any(kw in lower for kw in _PERFORMANCE_KEYWORDS_EN | _PERFORMANCE_KEYWORDS_VI):
        return "performance"
    if any(kw in lower for kw in _RECOMMENDATION_KEYWORDS_EN | _RECOMMENDATION_KEYWORDS_VI):
        return "recommendation"
    if any(kw in lower for kw in _TUTORING_KEYWORDS_EN | _TUTORING_KEYWORDS_VI):
        return "tutoring"
    return "general"


def _is_tutoring_intent(text: str) -> bool:
    """Kept for backwards compatibility — prefer _detect_intent."""
    return _detect_intent(text) == "tutoring"


# ── LangChain message converter ───────────────────────────────────────────────

def _to_lc_messages(msgs: list[Any]) -> list:
    result = []
    for m in msgs:
        role = m.role if hasattr(m, "role") else m.get("role", "")
        content = m.content if hasattr(m, "content") else m.get("content", "")
        if role == "user":
            result.append(HumanMessage(content=content or ""))
        elif role == "assistant":
            result.append(AIMessage(content=content or ""))
        elif role == "system":
            result.append(SystemMessage(content=content or ""))
        elif role == "tool":
            result.append(ToolMessage(content=content or "", tool_call_id=getattr(m, "tool_call_id", "") or ""))
    return result


# ── Tool factory ──────────────────────────────────────────────────────────────

def make_tools(student_id: int) -> list:
    """Return LangChain tools with student_id pre-bound via closure."""

    @tool
    async def get_student_profile() -> str:
        """Retrieve the student's full profile including enrollments, risk tier, risk score, risk flags, VLE engagement summary, and prerequisite knowledge gaps."""
        db = get_db()
        if db is not None:
            doc = await db.students.find_one({"student_id": student_id})
            data = doc or MOCK_STUDENT
        else:
            data = MOCK_STUDENT
        return json.dumps({k: v for k, v in data.items() if k != "_id"}, ensure_ascii=False, default=str)

    @tool
    async def get_assignments() -> str:
        """Retrieve all assessments for the student: TMA, CMA, and Exam types with due dates, weights, scores, and submission status. Unsubmitted items have submitted_date=null."""
        db = get_db()
        if db is not None:
            doc = await db.students.find_one({"student_id": student_id})
            profile = doc or MOCK_STUDENT
        else:
            profile = MOCK_STUDENT
        assessments = []
        for enrollment in profile.get("enrollments", []):
            module = enrollment.get("code_module", "")
            module_title = enrollment.get("title", "")
            for a in enrollment.get("assessments", []):
                assessments.append(
                    {**a, "module": module, "module_title": module_title})
        return json.dumps(assessments, ensure_ascii=False, default=str)

    @tool
    async def get_schedule() -> str:
        """Retrieve the student's current weekly timetable: lectures, lab sessions, group discussions, upcoming assignment deadlines, and exams with urgency flags."""
        db = get_db()
        if db is not None:
            doc = await db.timetable_blocks.find_one({"student_id": student_id})
            data = doc or MOCK_SCHEDULE
        else:
            data = MOCK_SCHEDULE
        return json.dumps({k: v for k, v in data.items() if k != "_id"}, ensure_ascii=False, default=str)

    @tool
    async def get_study_plan() -> str:
        """Retrieve the student's SM-2 spaced repetition study plan sessions with subject, type, duration, day, time, and interval."""
        db = get_db()
        if db is not None:
            doc = await db.study_plans.find_one({"student_id": student_id})
            data = doc.get("sessions", MOCK_STUDY_PLAN) if doc else MOCK_STUDY_PLAN
        else:
            data = MOCK_STUDY_PLAN
        return json.dumps(data, ensure_ascii=False, default=str)

    @tool
    async def update_study_plan(sessions: list) -> str:
        """Replace the student's entire study plan with a new list of sessions. Each session needs: subject (str), type (review/new/practice/spaced_rep/assignment), duration (int minutes), day (str), time (str HH:MM), sm2_interval (int or null)."""
        db = get_db()
        if db is not None:
            await db.study_plans.update_one(
                {"student_id": student_id},
                {"$set": {"sessions": sessions}},
                upsert=True,
            )
            return json.dumps({"status": "ok", "count": len(sessions)})
        return json.dumps({"status": "mock_mode"})

    @tool
    async def create_reminder(title: str, body: str, type: str = "reminder") -> str:
        """Create a notification/reminder for the student. type can be: reminder, alert, intervention."""
        db = get_db()
        from notify_schedule import compute_send_at
        notif = {
            "student_id": student_id,
            "type": type,
            "payload": {"title": title, "body": body},
            "read": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        send_at = compute_send_at(type)
        if send_at:
            notif["send_at"] = send_at
        if db is not None:
            await db.notifications.insert_one(notif)
            return json.dumps({"status": "ok"})
        return json.dumps({"status": "mock_mode"})

    @tool
    async def mark_assignment_complete(module_code: str, assessment_type: str) -> str:
        """Mark an assignment as submitted/complete. module_code is the module (e.g. BBB), assessment_type is TMA/CMA/Exam."""
        db = get_db()
        if db is not None:
            submitted = datetime.now(timezone.utc).isoformat()
            await db.students.update_one(
                {"student_id": student_id},
                {"$set": {"enrollments.$[e].assessments.$[a].submitted_date": submitted}},
                array_filters=[
                    {"e.code_module": module_code},
                    {"a.type": assessment_type},
                ],
            )
            return json.dumps({"status": "ok"})
        return json.dumps({"status": "mock_mode"})

    @tool
    async def save_study_note(subject: str, title: str, content: str) -> str:
        """Save a study note or summary for the student. subject is the topic area, title is a short heading, content is the note body."""
        db = get_db()
        note = {
            "student_id": student_id,
            "subject": subject,
            "title": title,
            "content": content,
            "type": "note",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        if db is not None:
            await db.resources.insert_one(note)
            return json.dumps({"status": "ok"})
        return json.dumps({"status": "mock_mode"})

    @tool
    async def get_knowledge_state() -> str:
        """Retrieve all concept mastery probabilities for the student (0.0–1.0 scale). Use this to understand what the student knows well vs. needs to review."""
        db = get_db()
        if db is not None:
            doc = await db.knowledge_states.find_one({"student_id": student_id})
            if doc:
                return json.dumps({k: v for k, v in doc.get("states", {}).items()}, ensure_ascii=False)
        return json.dumps(MOCK_KNOWLEDGE_STATES.get("states", {}), ensure_ascii=False)

    @tool
    async def update_knowledge_state(concept: str, evidence_type: str, score: float) -> str:
        """Update mastery for a concept after a learning event.
        concept: the concept name (e.g. 'Hồi quy tuyến tính').
        evidence_type: quiz | assignment | self_report | tutor_interaction.
        score: observed performance 0.0–1.0."""
        db = get_db()
        if db is not None:
            existing = await db.knowledge_states.find_one({"student_id": student_id})
            states = existing.get("states", {}) if existing else {}
            current = states.get(concept, {}).get("mastery", 0.5)
            new_mastery = update_mastery(current, evidence_type, score)
            states[concept] = {
                "mastery": new_mastery,
                "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "evidence_count": states.get(concept, {}).get("evidence_count", 0) + 1,
            }
            await db.knowledge_states.update_one(
                {"student_id": student_id},
                {"$set": {"states": states}},
                upsert=True,
            )
            return json.dumps({"status": "ok", "concept": concept, "mastery": new_mastery})
        return json.dumps({"status": "mock_mode"})

    @tool
    async def get_resources(topic: str = "") -> str:
        """Retrieve learning resources, optionally filtered by a topic keyword. Returns title, type, module, and url."""
        db = get_db()
        if db is not None:
            query = {"student_id": student_id}
            if topic:
                query["$or"] = [
                    {"title": {"$regex": topic, "$options": "i"}},
                    {"subject": {"$regex": topic, "$options": "i"}},
                ]
            cursor = db.resources.find(query).limit(10)
            docs = await cursor.to_list(length=10)
            for d in docs:
                d.pop("_id", None)
            if docs:
                return json.dumps(docs, ensure_ascii=False, default=str)
        # Mock fallback: filter by keyword
        resources = MOCK_RESOURCES
        if topic:
            tl = topic.lower()
            resources = [r for r in resources if tl in r.get("title", "").lower()]
        return json.dumps(resources, ensure_ascii=False)

    @tool
    async def break_down_assignment(id_assessment: int, milestones: list) -> str:
        """Store agent-generated milestones for an assignment.
        milestones: list of {id (str), title (str), due_offset_days (int), status (str: pending|in_progress|done|skipped)}.
        due_offset_days is relative to the assignment due date (e.g. -7 = 7 days before due)."""
        db = get_db()
        # Get assignment info for context
        profile = MOCK_STUDENT
        if db is not None:
            doc = await db.students.find_one({"student_id": student_id})
            if doc:
                profile = doc
        module = ""
        title = f"Assessment {id_assessment}"
        for enrollment in profile.get("enrollments", []):
            for a in enrollment.get("assessments", []):
                if a.get("id_assessment") == id_assessment:
                    module = enrollment.get("code_module", "")
                    title = f"{a.get('type', 'Assignment')} — {module}"
        record = {
            "student_id": student_id,
            "id_assessment": id_assessment,
            "module": module,
            "title": title,
            "milestones": milestones,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        if db is not None:
            await db.assignment_milestones.update_one(
                {"student_id": student_id, "id_assessment": id_assessment},
                {"$set": record},
                upsert=True,
            )
            return json.dumps({"status": "ok", "count": len(milestones)})
        return json.dumps({"status": "mock_mode"})

    @tool
    async def get_assignment_milestones(id_assessment: int) -> str:
        """Retrieve the milestone list for a specific assessment."""
        db = get_db()
        if db is not None:
            doc = await db.assignment_milestones.find_one(
                {"student_id": student_id, "id_assessment": id_assessment}
            )
            if doc:
                doc.pop("_id", None)
                return json.dumps(doc, ensure_ascii=False, default=str)
        # Mock fallback
        for m in MOCK_MILESTONES:
            if m["id_assessment"] == id_assessment:
                return json.dumps({k: v for k, v in m.items() if k != "_id"}, ensure_ascii=False)
        return json.dumps({"milestones": []})

    @tool
    async def update_milestone_status(id_assessment: int, milestone_id: str, status: str) -> str:
        """Update the status of a single milestone. status must be one of: pending | in_progress | done | skipped."""
        db = get_db()
        if db is not None:
            await db.assignment_milestones.update_one(
                {"student_id": student_id, "id_assessment": id_assessment, "milestones.id": milestone_id},
                {"$set": {"milestones.$.status": status}},
            )
            return json.dumps({"status": "ok"})
        return json.dumps({"status": "mock_mode"})

    @tool
    async def get_course_recommendations() -> str:
        """Get recommended next courses based on current mastery and prerequisite thresholds.
        Returns courses split into 'recommended' (all prereqs met) and 'not_ready' (with gap details)."""
        from agent.course_recommendation import recommend_courses
        result = await recommend_courses(student_id)
        return json.dumps(result, ensure_ascii=False)

    return [
        get_student_profile,
        get_assignments,
        get_schedule,
        get_study_plan,
        update_study_plan,
        create_reminder,
        mark_assignment_complete,
        save_study_note,
        get_knowledge_state,
        update_knowledge_state,
        get_resources,
        break_down_assignment,
        get_assignment_milestones,
        update_milestone_status,
        get_course_recommendations,
    ]
