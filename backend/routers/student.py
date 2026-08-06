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
    doc = await db.students.find_one({"student_id": student_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Student not found")
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
