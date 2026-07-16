# ── student.py ────────────────────────────────────────────────────────────────
from fastapi import APIRouter
from db.mongodb import get_db
from db.mock_data import MOCK_STUDENT, MOCK_KNOWLEDGE_STATES, MOCK_RISK_HISTORY

router = APIRouter()

@router.get("/{student_id}")
async def get_student(student_id: int):
    db = get_db()
    if db is None:
        return MOCK_STUDENT
    doc = await db.students.find_one({"student_id": student_id})
    if not doc:
        return MOCK_STUDENT
    doc["_id"] = str(doc["_id"])
    return doc


@router.get("/{student_id}/knowledge")
async def get_knowledge(student_id: int):
    """Return per-concept mastery states for the student."""
    db = get_db()
    if db is None:
        return MOCK_KNOWLEDGE_STATES.get("states", {})
    doc = await db.knowledge_states.find_one({"student_id": student_id})
    if not doc:
        return MOCK_KNOWLEDGE_STATES.get("states", {})
    return doc.get("states", {})


@router.get("/{student_id}/risk-history")
async def get_risk_history(student_id: int):
    """Return weekly risk score snapshots for the student."""
    db = get_db()
    if db is None:
        return MOCK_RISK_HISTORY.get("entries", [])
    doc = await db.risk_history.find_one({"student_id": student_id})
    if not doc:
        return MOCK_RISK_HISTORY.get("entries", [])
    return doc.get("entries", [])
