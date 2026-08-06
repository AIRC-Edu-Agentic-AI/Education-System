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
        pres = "2013J" if str(student_id).startswith("2013") else ("2014J" if str(student_id).startswith("2014") else "2013J")
        return {
            "_id": f"student_{student_id}",
            "auth0_id": f"auth0|student_{student_id}",
            "student_id": student_id,
            "full_name": f"Sinh viên {student_id}",
            "short_name": f"SV {student_id}",
            "demographics": {
                "gender": "M",
                "age_band": "18-25",
                "region": "Hà Nội",
                "highest_education": "HE Qualification",
                "imdBand": "20-30%",
                "disability": False,
                "num_prev_attempts": 0,
                "studied_credits": 60,
            },
            "enrollments": [
                {
                    "code_module": "AAA",
                    "code_presentation": pres,
                    "title": f"Môn học AAA ({pres})",
                    "module_length": 30,
                    "registration_date": -15,
                    "unregistration_date": None,
                    "final_result": None,
                    "assessments": [],
                    "vle_summary": {},
                }
            ],
            "risk": {"tier": 0, "computed_at": datetime.now(timezone.utc).isoformat()},
            "prerequisite_gaps": []
        }
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
    return doc.get("enrollments", [])


@router.get("/{student_id}/assignments")
async def get_student_assignments(student_id: int, code_module: Optional[str] = None):
    """
    BR13: Lay danh sach bai tap cua sinh vien theo cac khoa hoc dang ky.
    Ket hop: assessments embedded trong enrollments + assignment_milestones.
    
    Query params:
      code_module: loc theo ma mon hoc cu the
    """
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
            # Lay milestone neu co
            milestone_doc = None
            id_assessment = a.get("id_assessment") or a.get("id_assessment")
            if id_assessment:
                milestone_doc = await db.assignment_milestones.find_one(
                    {"student_id": student_id, "id_assessment": id_assessment}
                )

            # Lay submission neu co
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
