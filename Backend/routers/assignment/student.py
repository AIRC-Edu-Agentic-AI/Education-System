from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel

from db.mongodb import get_db
from db.mock_data import MOCK_STUDENT, MOCK_KNOWLEDGE_STATES, MOCK_RISK_HISTORY
from db.submissions import get_submission, submit_assignment
from db.event_logging import log_event

router = APIRouter()


class StudentAssignmentQuery(BaseModel):
    student_id: int
    code_module: Optional[str] = None


class SubmitAssignmentRequest(BaseModel):
    content: str


def _serialize_student(doc: dict) -> dict:
    if doc is None:
        return {}
    doc = dict(doc)
    doc["_id"] = str(doc.get("_id", ""))
    return doc


@router.get("/{student_id}/assignments")
async def get_student_assignments(student_id: int, code_module: Optional[str] = None):
    db = get_db()
    if db is None:
        return []

    doc = await db.students.find_one(
        {"student_id": student_id},
        {"_id": 0, "enrollments": 1}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Student not found")

    enrollments = doc.get("enrollments", [])
    result: List[Dict[str, Any]] = []

    for enrollment in enrollments:
        module = enrollment.get("code_module")
        if code_module and module != code_module:
            continue

        assessments = enrollment.get("assessments", [])
        for a in assessments:
            id_assessment = a.get("id_assessment")
            milestone_doc = None
            if id_assessment:
                milestone_doc = await db.assignment_milestones.find_one(
                    {"student_id": student_id, "id_assessment": id_assessment}
                )

            submission_doc = None
            if id_assessment:
                submission_doc = await db.submissions.find_one(
                    {"student_id": student_id, "id_assessment": id_assessment}
                )

            result.append({
                "id_assessment": id_assessment,
                "code_module": module,
                "code_presentation": enrollment.get("code_presentation"),
                "course_title": enrollment.get("title"),
                "type": a.get("assessment_type") or a.get("type"),
                "due_date": a.get("date_due") or a.get("due_date"),
                "weight": a.get("weight"),
                "score": a.get("score"),
                "date_submitted": a.get("date_submitted") or a.get("submitted_date"),
                "is_banked": a.get("is_banked", False),
                "milestones": milestone_doc.get("milestones", []) if milestone_doc else [],
                "submission": {
                    "status": submission_doc.get("status"),
                    "submitted_at": str(submission_doc.get("submitted_at", "")),
                    "file_name": submission_doc.get("file_name"),
                    "feedback": submission_doc.get("feedback"),
                } if submission_doc else None,
            })

    return result


@router.post("/{student_id}/assignments/{id_assessment}/submit", status_code=201)
async def submit_assignment_for_student(student_id: int, id_assessment: int, payload: SubmitAssignmentRequest):
    db = get_db()
    submission = await submit_assignment(db, student_id, id_assessment, payload.content)

    await log_event(
        None,
        "assignment_submitted",
        actor_id=str(student_id),
        target_id=str(id_assessment),
        payload={"student_id": student_id, "id_assessment": id_assessment},
        source="assignments",
    )
    return submission


@router.get("/{student_id}/assignments/{id_assessment}/submission")
async def get_student_assignment_submission(student_id: int, id_assessment: int):
    db = get_db()
    submission = await get_submission(db, student_id, id_assessment)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission
