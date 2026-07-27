"""
Teacher Classroom Management Router.

Handles:
- BR28: Lecturer chi quan ly cac khoa hoc duoc phan cong
- BR29: Lecturer xem danh sach SV thuoc khoa hoc minh phu trach
- BR34-35: Dashboard theo doi du lieu lop

Endpoints:
  GET    /api/classrooms                        - Danh sach lop hoc cua GV
  POST   /api/classrooms                        - Tao lop hoc moi
  GET    /api/classrooms/{id}                   - Chi tiet lop hoc
  PUT    /api/classrooms/{id}                   - Cap nhat lop hoc
  DELETE /api/classrooms/{id}                   - Xoa lop hoc
  GET    /api/classrooms/{id}/students          - Danh sach SV trong lop
  GET    /api/classrooms/{id}/students/risk     - Danh sach SV trong lop + risk info
  POST   /api/classrooms/{id}/students          - Them SV vao lop
  DELETE /api/classrooms/{id}/students/{sid}    - Xoa SV khoi lop
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from db.mongodb import db_state
from db.utils import serialize_doc

router = APIRouter()


def get_db():
    db = db_state.get("db")
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    return db


def _parse_oid(classroom_id: str) -> ObjectId:
    try:
        return ObjectId(classroom_id)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=400, detail=f"Invalid classroom id: {classroom_id}")


# ─── Pydantic Models ───────────────────────────────────────────────────────────

class ClassroomCreatePayload(BaseModel):
    name: str
    module: str
    code_presentation: str
    teacher_id: str
    description: Optional[str] = None
    student_ids: Optional[List[int]] = None


class ClassroomUpdatePayload(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    teacher_id: Optional[str] = None
    status: Optional[str] = None


class AddStudentsPayload(BaseModel):
    student_ids: List[int]


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("")
async def list_classrooms(
    module: Optional[str] = Query(None),
    presentation: Optional[str] = Query(None),
    teacher_id: Optional[str] = Query(None),
) -> List[Dict[str, Any]]:
    """
    Lay danh sach tat ca lop hoc.
    Filter theo module, presentation, hoac teacher_id neu co.
    """
    try:
        db = get_db()
        query: Dict[str, Any] = {"status": {"$ne": "deleted"}}
        if module:
            query["module"] = module
        if presentation:
            query["code_presentation"] = presentation
        if teacher_id:
            query["teacher_id"] = teacher_id

        docs = await db["classrooms"].find(query).sort("name", 1).to_list(None)
        return serialize_doc(docs)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.post("", status_code=201)
async def create_classroom(payload: ClassroomCreatePayload) -> Dict[str, Any]:
    """
    Tao lop hoc moi.
    BR28: Chi teacher duoc phan cong moi co quyen tao.
    """
    try:
        db = get_db()
        now = datetime.now(timezone.utc).isoformat()
        doc = {
            "name": payload.name,
            "module": payload.module,
            "code_presentation": payload.code_presentation,
            "teacher_id": payload.teacher_id,
            "description": payload.description or "",
            "student_ids": payload.student_ids or [],
            "status": "active",
            "created_at": now,
            "updated_at": now,
        }
        result = await db["classrooms"].insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        return doc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.get("/{classroom_id}")
async def get_classroom(classroom_id: str) -> Dict[str, Any]:
    """Chi tiet 1 lop hoc."""
    try:
        db = get_db()
        oid = _parse_oid(classroom_id)
        doc = await db["classrooms"].find_one({"_id": oid, "status": {"$ne": "deleted"}})
        if not doc:
            raise HTTPException(status_code=404, detail="Classroom not found")
        return serialize_doc(doc)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.put("/{classroom_id}")
async def update_classroom(classroom_id: str, payload: ClassroomUpdatePayload) -> Dict[str, Any]:
    """Cap nhat thong tin lop hoc."""
    try:
        db = get_db()
        oid = _parse_oid(classroom_id)
        update: Dict[str, Any] = {"updated_at": datetime.now(timezone.utc).isoformat()}
        if payload.name is not None:
            update["name"] = payload.name
        if payload.description is not None:
            update["description"] = payload.description
        if payload.teacher_id is not None:
            update["teacher_id"] = payload.teacher_id
        if payload.status is not None:
            if payload.status not in ("active", "archived", "deleted"):
                raise HTTPException(status_code=400, detail="status phai la: active, archived, hoac deleted")
            update["status"] = payload.status

        result = await db["classrooms"].update_one({"_id": oid}, {"$set": update})
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Classroom not found")
        doc = await db["classrooms"].find_one({"_id": oid})
        return serialize_doc(doc)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.delete("/{classroom_id}")
async def delete_classroom(classroom_id: str) -> Dict[str, Any]:
    """Xoa mem lop hoc (soft delete)."""
    try:
        db = get_db()
        oid = _parse_oid(classroom_id)
        result = await db["classrooms"].update_one(
            {"_id": oid},
            {"$set": {"status": "deleted", "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Classroom not found")
        return {"ok": True, "classroom_id": classroom_id}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.get("/{classroom_id}/students")
async def get_classroom_students(classroom_id: str) -> Dict[str, Any]:
    """
    BR29: Lay danh sach SV thuoc lop hoc.
    Ket hop thong tin day du tu students collection.
    """
    try:
        db = get_db()
        oid = _parse_oid(classroom_id)
        classroom = await db["classrooms"].find_one({"_id": oid, "status": {"$ne": "deleted"}})
        if not classroom:
            raise HTTPException(status_code=404, detail="Classroom not found")

        student_ids = classroom.get("student_ids", [])
        if not student_ids:
            return {"classroom": serialize_doc(classroom), "students": [], "count": 0}

        # Lay thong tin SV tu students collection
        student_docs = await db["students"].find(
            {"student_id": {"$in": student_ids}},
            {"_id": 0, "student_id": 1, "full_name": 1, "email": 1, "risk": 1, "is_active": 1, "avatar_url": 1}
        ).to_list(None)



        return {
            "classroom": serialize_doc(classroom),
            "students": student_docs,
            "count": len(student_docs),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.get("/{classroom_id}/students/risk")
async def get_classroom_students_risk(classroom_id: str) -> Dict[str, Any]:
    """
    Lay danh sach SV trong lop kem theo thong tin rui ro day du.
    Dung cho giao dien Risk Management cua GV.
    """
    try:
        db = get_db()
        oid = _parse_oid(classroom_id)
        classroom = await db["classrooms"].find_one({"_id": oid, "status": {"$ne": "deleted"}})
        if not classroom:
            raise HTTPException(status_code=404, detail="Classroom not found")

        student_ids = classroom.get("student_ids", [])
        if not student_ids:
            return {"students": [], "count": 0}

        student_docs = await db["students"].find(
            {"student_id": {"$in": student_ids}},
            {
                "_id": 0,
                "student_id": 1,
                "full_name": 1,
                "email": 1,
                "risk": 1,
                "enrollments": 1,
            }
        ).to_list(None)

        # Enrich risk history
        result = []
        for s in student_docs:
            risk = s.get("risk", {}) or {}
            result.append({
                "student_id": s["student_id"],
                "full_name": s.get("full_name"),
                "email": s.get("email"),
                "risk_score": risk.get("score"),
                "risk_tier": risk.get("tier"),
                "risk_flags": risk.get("flags", []),
                "risk_computed_at": str(risk.get("computed_at", "")),
                "enrollment_count": len(s.get("enrollments", [])),
            })

        result.sort(key=lambda x: (x.get("risk_score") or 0), reverse=True)
        return {
            "classroom_id": classroom_id,
            "classroom_name": classroom.get("name"),
            "students": result,
            "count": len(result),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.post("/{classroom_id}/students", status_code=201)
async def add_students_to_classroom(classroom_id: str, payload: AddStudentsPayload) -> Dict[str, Any]:
    """Them 1 hoac nhieu SV vao lop hoc."""
    try:
        db = get_db()
        oid = _parse_oid(classroom_id)
        result = await db["classrooms"].update_one(
            {"_id": oid, "status": {"$ne": "deleted"}},
            {
                "$addToSet": {"student_ids": {"$each": payload.student_ids}},
                "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
            }
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Classroom not found")
        return {"ok": True, "added": payload.student_ids, "classroom_id": classroom_id}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.delete("/{classroom_id}/students/{student_id}")
async def remove_student_from_classroom(classroom_id: str, student_id: int) -> Dict[str, Any]:
    """Xoa SV khoi lop hoc."""
    try:
        db = get_db()
        oid = _parse_oid(classroom_id)
        result = await db["classrooms"].update_one(
            {"_id": oid, "status": {"$ne": "deleted"}},
            {
                "$pull": {"student_ids": student_id},
                "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
            }
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Classroom not found")
        return {"ok": True, "removed_student_id": student_id, "classroom_id": classroom_id}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc
