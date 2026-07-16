"""Course Recommendation Agent.

Rule-based: checks prerequisite mastery thresholds before recommending a course.
No LLM needed — deterministic logic over KT state.
"""
from agent.base import get_knowledge_state_stub
from db.mock_data import MOCK_NEXT_COURSES

PREREQ_THRESHOLD = 0.5


async def recommend_courses(student_id: int) -> dict:
    """Return courses split into ready (all prereqs met) and not_ready (gaps listed)."""
    kt = await get_knowledge_state_stub(student_id)

    recommended: list[dict] = []
    not_ready: list[dict] = []

    for course in MOCK_NEXT_COURSES:
        prereqs = course.get("prerequisites", [])
        missing = [p for p in prereqs if kt.get(p, 0.0) < PREREQ_THRESHOLD]
        if missing:
            not_ready.append({**course, "missing_prereqs": missing,
                               "mastery": {p: kt.get(p, 0.0) for p in prereqs}})
        else:
            recommended.append(course)

    return {"recommended": recommended, "not_ready": not_ready}
