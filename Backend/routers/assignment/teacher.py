from fastapi import APIRouter, HTTPException
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from bson import ObjectId
from bson.errors import InvalidId

from db.mongodb import get_db
from db.event_logging import log_event

router = APIRouter()


# ── Models ──────────────────────────────────────────────────────────────────

class CreateAssignmentRequest(BaseModel):
    title: str
    description: str
    type: str = "TMA"
    weight: float = 10.0
    due_date: int
    allowed_formats: List[str] = ["pdf", "docx"]
    max_file_size_mb: int = 25
    teacher_id: Optional[str] = None


class UpdateAssignmentRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    weight: Optional[float] = None
    due_date: Optional[int] = None
    allowed_formats: Optional[List[str]] = None
    max_file_size_mb: Optional[int] = None
    status: Optional[str] = None


class CreateClassroomAssignmentRequest(BaseModel):
    code_module: str
    title: str
    description: str
    type: str = "TMA"
    weight: float = 10.0
    due_date: int
    allowed_formats: List[str] = ["pdf", "docx"]
    max_file_size_mb: int = 25
    teacher_id: Optional[str] = None


class UpdateClassroomAssignmentRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    weight: Optional[float] = None
    due_date: Optional[int] = None
    allowed_formats: Optional[List[str]] = None
    max_file_size_mb: Optional[int] = None
    status: Optional[str] = None


class GradeSubmissionRequest(BaseModel):
    score: float
    feedback: Optional[str] = None


# ── Helper Functions ────────────────────────────────────────────────────────

def _parse_classroom_id(classroom_id: str) -> ObjectId:
    try:
        return ObjectId(classroom_id)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=400, detail=f"Invalid classroom id: {classroom_id}")


async def _load_assignments(module: str, presentation: str):
    db = get_db()
    if db is None:
        return []
    docs = await db.assignments.find({"code_module": module, "code_presentation": presentation}).to_list(None)
    for d in docs:
        d["_id"] = str(d.get("_id", ""))
    return docs


async def _create_assignment(module: str, presentation: str, payload: CreateAssignmentRequest):
    db = get_db()
    if db is None:
        return {"ok": True, "mock": True}
    now = datetime.now().isoformat()
    id_assessment = int(datetime.now().timestamp() * 1000)
    doc = {
        "id_assessment": id_assessment,
        "code_module": module,
        "code_presentation": presentation,
        "title": payload.title,
        "description": payload.description,
        "type": payload.type,
        "weight": payload.weight,
        "due_date": payload.due_date,
        "allowed_formats": payload.allowed_formats,
        "max_file_size_mb": payload.max_file_size_mb,
        "teacher_id": payload.teacher_id,
        "created_at": now,
        "updated_at": now,
        "status": "active",
    }
    result = await db.assignments.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    await log_event(
        None,
        "assignment_created",
        actor_id=payload.teacher_id,
        target_id=str(id_assessment),
        payload={"code_module": module, "code_presentation": presentation},
        source="assignments",
    )
    return doc


# ── Teacher: Grading & Submissions (must be before /{module}/{presentation}) ─

@router.get("/{id_assessment}/all-submissions")
async def get_all_submissions_for_assessment(id_assessment: int):
    """Get all submissions for an assessment across all students."""
    db = get_db()
    if db is None:
        return []
    docs = await db.submissions.find({"id_assessment": id_assessment}).to_list(None)
    for d in docs:
        d["_id"] = str(d.get("_id", ""))
    return docs


@router.post("/{id_assessment}/grade/{student_id}")
async def grade_submission(id_assessment: int, student_id: int, payload: GradeSubmissionRequest):
    """Grade a student's submission."""
    db = get_db()
    if db is None:
        return {"ok": True, "mock": True}

    if payload.score < 0 or payload.score > 100:
        raise HTTPException(status_code=400, detail="Score must be between 0 and 100")

    update = {
        "score": payload.score,
        "status": "graded",
        "updated_at": datetime.now().isoformat(),
    }
    if payload.feedback is not None:
        update["feedback"] = payload.feedback

    result = await db.submissions.update_one(
        {"id_assessment": id_assessment, "student_id": student_id},
        {"$set": update},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Submission not found")

    await db.students.update_one(
        {"student_id": student_id, "enrollments.assessments.id_assessment": id_assessment},
        {"$set": {"enrollments.$[e].assessments.$[a].score": payload.score}},
        array_filters=[{"a.id_assessment": id_assessment}],
    )

    await log_event(
        None,
        "assignment_graded",
        actor_id=str(student_id),
        target_id=str(id_assessment),
        payload={"score": payload.score, "student_id": student_id},
        source="assignments",
    )
    return {"ok": True, "student_id": student_id, "id_assessment": id_assessment, "score": payload.score}


@router.get("/{id_assessment}/submission/{student_id}")
async def get_student_submission_for_teacher(id_assessment: int, student_id: int):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    doc = await db.submissions.find_one({"id_assessment": id_assessment, "student_id": student_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Submission not found")
    doc["_id"] = str(doc.get("_id", ""))
    return doc


# ── Teacher: Assignment CRUD (Module/Presentation) ────────────────────────

@router.get("")
async def list_assignments(module: str, presentation: str):
    """List all assignments for a module and presentation."""
    return await _load_assignments(module, presentation)


@router.get("/{module}/{presentation}")
async def list_assignments_by_path(module: str, presentation: str):
    """List all assignments for a module and presentation via path params."""
    return await _load_assignments(module, presentation)


@router.post("", status_code=201)
async def create_assignment_for_course(module: str, presentation: str, payload: CreateAssignmentRequest):
    """Create a new assignment for a module/presentation via query params."""
    return await _create_assignment(module, presentation, payload)


@router.post("/{module}/{presentation}", status_code=201)
async def create_assignment_for_course_by_path(module: str, presentation: str, payload: CreateAssignmentRequest):
    """Create a new assignment for a module/presentation via path params."""
    return await _create_assignment(module, presentation, payload)


@router.patch("/{id_assessment}")
async def update_assignment(id_assessment: int, payload: UpdateAssignmentRequest):
    """Update assignment details."""
    db = get_db()
    if db is None:
        return {"ok": True, "mock": True}

    update_fields = {"updated_at": datetime.now().isoformat()}
    if payload.title is not None:
        update_fields["title"] = payload.title
    if payload.description is not None:
        update_fields["description"] = payload.description
    if payload.type is not None:
        update_fields["type"] = payload.type
    if payload.weight is not None:
        update_fields["weight"] = payload.weight
    if payload.due_date is not None:
        update_fields["due_date"] = payload.due_date
    if payload.allowed_formats is not None:
        update_fields["allowed_formats"] = payload.allowed_formats
    if payload.max_file_size_mb is not None:
        update_fields["max_file_size_mb"] = payload.max_file_size_mb
    if payload.status is not None:
        update_fields["status"] = payload.status

    if len(update_fields) == 1:
        raise HTTPException(status_code=400, detail="Nothing to update")

    result = await db.assignments.update_one(
        {"id_assessment": id_assessment},
        {"$set": update_fields},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Assignment not found")

    doc = await db.assignments.find_one({"id_assessment": id_assessment})
    if doc is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    doc["_id"] = str(doc.get("_id", ""))
    await log_event(
        None,
        "assignment_updated",
        target_id=str(id_assessment),
        payload={"updated_fields": list(update_fields.keys())},
        source="assignments",
    )
    return doc


@router.delete("/{id_assessment}")
async def delete_assignment(id_assessment: int):
    """Delete an assignment by id_assessment."""
    db = get_db()
    if db is None:
        return {"ok": True, "mock": True}
    result = await db.assignments.delete_one({"id_assessment": id_assessment})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Assignment not found")
    await log_event(
        None,
        "assignment_deleted",
        target_id=str(id_assessment),
        source="assignments",
    )
    return {"ok": True, "deleted": id_assessment}


# ── Teacher: Classroom Assignment Management ────────────────────────────────

@router.get("/class/{classroom_id}/assignments")
async def get_class_assignments(classroom_id: str):
    """Get all assignments created for a classroom."""
    db = get_db()
    if db is None:
        return []
    oid = _parse_classroom_id(classroom_id)
    classroom = await db["classrooms"].find_one({"_id": oid, "status": {"$ne": "deleted"}})
    if classroom is None:
        raise HTTPException(status_code=404, detail="Classroom not found")

    docs = await db["assignments"].find({"classroom_id": classroom_id}).to_list(None)
    for d in docs:
        d["_id"] = str(d.get("_id", ""))
    return docs


@router.post("/class/{classroom_id}/assignments", status_code=201)
async def create_classroom_assignment(classroom_id: str, payload: CreateClassroomAssignmentRequest):
    """Create a new assignment for all students in a classroom."""
    db = get_db()
    if db is None:
        return {"ok": True, "mock": True}

    classroom = await db["classrooms"].find_one({"_id": classroom_id, "status": {"$ne": "deleted"}})
    if classroom is None:
        raise HTTPException(status_code=404, detail="Classroom not found")

    student_ids = classroom.get("student_ids", []) or []
    if not student_ids:
        raise HTTPException(status_code=400, detail="Classroom has no students")

    now = datetime.now().isoformat()
    id_assessment = int(datetime.now().timestamp() * 1000)
    doc = {
        "id_assessment": id_assessment,
        "code_module": payload.code_module,
        "title": payload.title,
        "description": payload.description,
        "type": payload.type,
        "weight": payload.weight,
        "due_date": payload.due_date,
        "allowed_formats": payload.allowed_formats,
        "max_file_size_mb": payload.max_file_size_mb,
        "teacher_id": payload.teacher_id,
        "classroom_id": classroom_id,
        "classroom_name": classroom.get("name"),
        "student_ids": student_ids,
        "created_at": now,
        "updated_at": now,
        "status": "active",
    }
    result = await db["assignments"].insert_one(doc)
    doc["_id"] = str(result.inserted_id)

    await log_event(
        None,
        "assignment_created",
        actor_id=payload.teacher_id,
        target_id=str(id_assessment),
        payload={"classroom_id": classroom_id, "code_module": payload.code_module, "student_count": len(student_ids)},
        source="assignments",
    )

    return doc


@router.put("/class/{classroom_id}/assignments/{id_assessment}")
async def update_classroom_assignment(classroom_id: str, id_assessment: int, payload: UpdateClassroomAssignmentRequest):
    """Update assignment details for a classroom assignment."""
    db = get_db()
    if db is None:
        return {"ok": True, "mock": True}

    classroom = await db["classrooms"].find_one({"_id": classroom_id, "status": {"$ne": "deleted"}})
    if classroom is None:
        raise HTTPException(status_code=404, detail="Classroom not found")

    update_fields = {"updated_at": datetime.now().isoformat()}
    if payload.title is not None:
        update_fields["title"] = payload.title
    if payload.description is not None:
        update_fields["description"] = payload.description
    if payload.type is not None:
        update_fields["type"] = payload.type
    if payload.weight is not None:
        update_fields["weight"] = payload.weight
    if payload.due_date is not None:
        update_fields["due_date"] = payload.due_date
    if payload.allowed_formats is not None:
        update_fields["allowed_formats"] = payload.allowed_formats
    if payload.max_file_size_mb is not None:
        update_fields["max_file_size_mb"] = payload.max_file_size_mb
    if payload.status is not None:
        update_fields["status"] = payload.status

    result = await db["assignments"].update_one(
        {"classroom_id": classroom_id, "id_assessment": id_assessment},
        {"$set": update_fields}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Assignment not found for classroom")

    await log_event(
        None,
        "assignment_updated",
        actor_id=payload.teacher_id,
        target_id=str(id_assessment),
        payload={"classroom_id": classroom_id},
        source="assignments",
    )

    doc = await db["assignments"].find_one({"classroom_id": classroom_id, "id_assessment": id_assessment})
    doc["_id"] = str(doc.get("_id", ""))
    return doc


@router.delete("/class/{classroom_id}/assignments/{id_assessment}")
async def delete_classroom_assignment(classroom_id: str, id_assessment: int):
    """Delete an assignment from a classroom."""
    db = get_db()
    if db is None:
        return {"ok": True, "mock": True}

    result = await db["assignments"].delete_one({"classroom_id": classroom_id, "id_assessment": id_assessment})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Assignment not found for classroom")

    await log_event(
        None,
        "assignment_deleted",
        target_id=str(id_assessment),
        payload={"classroom_id": classroom_id},
        source="assignments",
    )

    return {"ok": True, "deleted": id_assessment}
