"""Student router — endpoints cho Student Portal.

BR01-BR18 (Student business rules)

Endpoints:
  GET    /student/{student_id}                  - Thong tin sinh vien
  PATCH  /student/{student_id}/profile          - Cap nhat thong tin ca nhan (BR02-03)
  GET    /student/{student_id}/enrollments      - Danh sach mon hoc dang ky (BR07)
  GET    /student/{student_id}/assignments      - Danh sach bai tap cua SV (BR13)
  GET    /student/{student_id}/knowledge        - Trang thai kien thuc
  GET    /student/{student_id}/risk-history     - Lich su rui ro
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.mongodb import get_db
from db.mock_data import MOCK_STUDENT, MOCK_KNOWLEDGE_STATES, MOCK_RISK_HISTORY

router = APIRouter()


# ─── Pydantic Models ───────────────────────────────────────────────────────────

class StudentProfileUpdate(BaseModel):
    """
    BR02: Chi cho phep cap nhat cac truong duoc he thong cho phep.
    Cac truong nhu student_id, email khong duoc cap nhat qua day.
    """
    full_name: Optional[str] = None
    short_name: Optional[str] = None
    avatar_url: Optional[str] = None
    # demographics sub-fields (partial update)
    gender: Optional[str] = None
    region: Optional[str] = None


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _serialize_student(doc: dict) -> dict:
    """Serialize MongoDB student doc: convert _id and dates to strings."""
    if doc is None:
        return {}
    doc = dict(doc)
    doc["_id"] = str(doc.get("_id", ""))
    # Convert date fields in risk.computed_at
    risk = doc.get("risk", {})
    if risk and hasattr(risk.get("computed_at"), "isoformat"):
        risk["computed_at"] = risk["computed_at"].isoformat()
    return doc


def _build_assessment_payload(assignment_doc: Optional[dict] = None, module: Optional[str] = None, presentation: Optional[str] = None, fallback_assessment: Optional[dict] = None) -> dict:
    """Build a student-facing assessment payload from the shared assignments collection."""
    source = dict(assignment_doc or {})
    fallback = dict(fallback_assessment or {})

    if not source and not fallback:
        return {
            "id_assessment": 0,
            "type": "",
            "due_date": 0,
            "weight": 0.0,
            "score": None,
            "submitted_date": None,
            "is_banked": False,
        }

    id_assessment = source.get("id_assessment") or fallback.get("id_assessment") or 0
    assessment_type = source.get("type") or fallback.get("assessment_type") or fallback.get("type") or ""
    due_date = source.get("due_date") or source.get("date_due") or fallback.get("date_due") or fallback.get("due_date") or 0
    weight = source.get("weight") if source.get("weight") is not None else fallback.get("weight")
    score = fallback.get("score")
    submitted_date = fallback.get("date_submitted") or fallback.get("submitted_date")
    is_banked = fallback.get("is_banked", False)

    if isinstance(due_date, datetime):
        due_date = int(due_date.timestamp())
    elif isinstance(due_date, str):
        try:
            due_date = int(float(due_date))
        except ValueError:
            try:
                due_date = int(datetime.fromisoformat(due_date.replace("Z", "+00:00")).timestamp())
            except ValueError:
                due_date = 0

    return {
        "id_assessment": id_assessment,
        "code_module": module or source.get("code_module") or fallback.get("code_module"),
        "code_presentation": presentation or source.get("code_presentation") or fallback.get("code_presentation"),
        "type": assessment_type,
        "due_date": due_date,
        "weight": weight if weight is not None else 0.0,
        "score": score,
        "submitted_date": submitted_date,
        "is_banked": is_banked,
        "title": source.get("title") or fallback.get("title"),
        "description": source.get("description") or fallback.get("description"),
    }


async def _build_enrollments_payload(student_doc: dict, code_module: Optional[str] = None) -> List[dict]:
    """Attach assignments from the shared assignments collection into each enrollment."""
    db = get_db()
    enrollments = list(student_doc.get("enrollments", []) or [])
    student_id = student_doc.get("student_id")

    submission_by_assessment: dict = {}
    if db is not None and student_id is not None:
        submissions = await db.submissions.find({"student_id": student_id}).to_list(None)
        for sub in submissions:
            id_assessment = sub.get("id_assessment")
            if id_assessment is not None:
                submission_by_assessment[str(id_assessment)] = sub

    for enrollment in enrollments:
        module = enrollment.get("code_module")
        presentation = enrollment.get("code_presentation")
        if code_module and module != code_module:
            continue

        existing_assessments = list(enrollment.get("assessments", []) or [])
        if db is None:
            enrollment["assessments"] = [
                _build_assessment_payload(None, module, presentation, assessment)
                for assessment in existing_assessments
            ]
            continue

        assignment_filter = {"code_module": module}
        if presentation:
            assignment_filter["code_presentation"] = presentation

        assignment_docs = await db.assignments.find(assignment_filter).to_list(None)
        if assignment_docs:
            merged_assessments: List[dict] = []

            for assignment_doc in assignment_docs:
                fallback_assessment = next(
                    (
                        a for a in existing_assessments
                        if str(a.get("id_assessment")) == str(assignment_doc.get("id_assessment"))
                    ),
                    None,
                )
                id_assessment = assignment_doc.get("id_assessment")
                submission = submission_by_assessment.get(str(id_assessment))
                if submission:
                    fallback_assessment = dict(fallback_assessment or {})
                    fallback_assessment["id_assessment"] = id_assessment
                    fallback_assessment["submitted_date"] = (
                        submission.get("submitted_day")
                        or fallback_assessment.get("submitted_date")
                    )
                merged_assessments.append(
                    _build_assessment_payload(assignment_doc, module, presentation, fallback_assessment)
                )

            enrollment["assessments"] = merged_assessments
        else:
            enrollment["assessments"] = []
            for assessment in existing_assessments:
                id_assessment = assessment.get("id_assessment")
                submission = submission_by_assessment.get(str(id_assessment))
                fallback = dict(assessment)
                if submission:
                    fallback["submitted_date"] = (
                        submission.get("submitted_day")
                        or fallback.get("submitted_date")
                    )
                enrollment["assessments"].append(
                    _build_assessment_payload(None, module, presentation, fallback)
                )

    return enrollments


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/{student_id}")
async def get_student(student_id: int):
    """
    BR01: Lay thong tin ca nhan cua sinh vien.
    BR04: Chi xem ho so hoc tap cua chinh minh.
    """
    db = get_db()
    if db is None:
        return MOCK_STUDENT
    query = {"$or": [{"student_id": student_id}, {"student_id": str(student_id)}]}
    doc = await db.students.find_one(query)
    if not doc:
        raise HTTPException(status_code=404, detail="Student not found")

    doc["enrollments"] = await _build_enrollments_payload(doc)
    return _serialize_student(doc)


@router.patch("/{student_id}/profile")
async def update_student_profile(student_id: int, payload: StudentProfileUpdate):
    """
    BR02: Cap nhat thong tin ca nhan duoc phep.
    BR03: Thay doi duoc luu vao he thong sau khi xac nhan.
    """
    db = get_db()
    if db is None:
        return {"ok": True, "mock": True}

    # Kiem tra student ton tai
    student = await db.students.find_one({"student_id": student_id})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    update_fields: Dict[str, Any] = {
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    if payload.full_name is not None:
        update_fields["full_name"] = payload.full_name
    if payload.short_name is not None:
        update_fields["short_name"] = payload.short_name
    if payload.avatar_url is not None:
        update_fields["avatar_url"] = payload.avatar_url

    # Cap nhat demographics sub-fields
    demo_updates = {}
    if payload.gender is not None:
        demo_updates["demographics.gender"] = payload.gender
    if payload.region is not None:
        demo_updates["demographics.region"] = payload.region
    update_fields.update(demo_updates)

    await db.students.update_one(
        {"student_id": student_id},
        {"$set": update_fields}
    )

    doc = await db.students.find_one({"student_id": student_id})
    return _serialize_student(doc)


@router.get("/{student_id}/enrollments")
async def get_student_enrollments(student_id: int):
    """
    BR07: Lay danh sach khoa hoc da duoc phan cong hoac dang ky.
    Tra ve danh sach enrollments tu students collection.
    """
    db = get_db()
    if db is None:
        return MOCK_STUDENT.get("enrollments", [])

    doc = await db.students.find_one(
        {"student_id": student_id},
        {"_id": 0, "enrollments": 1}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Student not found")

    doc["enrollments"] = await _build_enrollments_payload(doc)
    return doc.get("enrollments", [])




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
