from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from bson import ObjectId
from bson.errors import InvalidId
import shutil
import os
import uuid

from db.mongodb import get_db
from db.mock_data import MOCK_STUDENT, MOCK_KNOWLEDGE_STATES, MOCK_RISK_HISTORY, MOCK_MILESTONES
from db.submissions import get_submission, submit_assignment
from db.event_logging import log_event
from routers.student import _build_enrollments_payload

router = APIRouter()


# ── Models ──────────────────────────────────────────────────────────────────

class StudentAssignmentQuery(BaseModel):
    student_id: int
    code_module: Optional[str] = None


class SubmitAssignmentRequest(BaseModel):
    student_id: int
    content: str = Field(..., min_length=1, max_length=8000)


class ClassCommentRequest(BaseModel):
    student_id: int
    content: str = Field(..., min_length=1, max_length=1000)


class MilestoneUpdateRequest(BaseModel):
    student_id: int
    id_assessment: int
    milestone_id: str
    status: str


def _serialize_student(doc: dict) -> dict:
    if doc is None:
        return {}
    doc = dict(doc)
    doc["_id"] = str(doc.get("_id", ""))
    return doc


# ── Student: Get Assignments & Submissions ──────────────────────────────────

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

    enrollments = await _build_enrollments_payload(doc, code_module)
    result: List[Dict[str, Any]] = []

    for enrollment in enrollments:
        module = enrollment.get("code_module")
        assessments = enrollment.get("assessments", [])
        for a in assessments:
            id_assessment = a.get("id_assessment")
            milestone_doc = None
            if id_assessment:
                milestone_doc = await db.assignments.find_one(
                    {"id_assessment": id_assessment}
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
                "type": a.get("type") or a.get("assessment_type"),
                "due_date": a.get("due_date"),
                "weight": a.get("weight"),
                "score": a.get("score"),
                "date_submitted": a.get("submitted_date"),
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


# ── Student: Milestones ─────────────────────────────────────────────────────

@router.get("/{id_assessment}/milestones")
async def get_milestones(id_assessment: int, student_id: int):
    """Return milestone list for an assignment. Empty list if none generated yet."""
    db = get_db()
    if db is not None:
        doc = await db.assignments.find_one(
            {"id_assessment": id_assessment}
        )
        if doc:
            doc["_id"] = str(doc["_id"])
            return {"id_assessment": id_assessment, "milestones": doc.get("milestones", [])}
        return {"id_assessment": id_assessment, "milestones": []}
    # Mock fallback
    for m in MOCK_MILESTONES:
        if m["id_assessment"] == id_assessment:
            return {k: v for k, v in m.items() if k != "_id"}
    return {"id_assessment": id_assessment, "milestones": []}


@router.post("/{id_assessment}/breakdown")
async def trigger_breakdown(id_assessment: int, student_id: int):
    """Trigger milestone generation. Returns existing milestones if already done."""
    db = get_db()
    # Return existing if already generated
    if db is not None:
        existing = await db.assignments.find_one(
            {"id_assessment": id_assessment}
        )
        if existing and existing.get("milestones"):
            return {"id_assessment": id_assessment, "milestones": existing.get("milestones", [])}
    else:
        for m in MOCK_MILESTONES:
            if m["id_assessment"] == id_assessment:
                return {k: v for k, v in m.items() if k != "_id"}

    # Generate via agent
    from agent.assignment_breakdown import run_breakdown
    await run_breakdown(student_id, id_assessment)

    # Return newly created milestones
    if db is not None:
        doc = await db.assignments.find_one(
            {"id_assessment": id_assessment}
        )
        if doc:
            return {"id_assessment": id_assessment, "milestones": doc.get("milestones", [])}
    return {"id_assessment": id_assessment, "milestones": [], "status": "processing"}


@router.patch("/milestone/status")
async def update_milestone_status(body: MilestoneUpdateRequest):
    """Update a single milestone status."""
    db = get_db()
    if db is None:
        return {"ok": True, "mock": True}
    await db.assignments.update_one(
        {
            "id_assessment": body.id_assessment,
            "milestones.id": body.milestone_id,
        },
        {"$set": {"milestones.$.status": body.status}},
    )
    return {"ok": True}


# ── Student: File Submissions ───────────────────────────────────────────────

@router.post("/{id_assessment}/submit-file")
async def submit_assignment_file(
    id_assessment: int,
    student_id: int = Form(...),
    file: UploadFile = File(...)
):
    """Submit assignment with PDF file."""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=500, detail="Database unavailable; cannot save submission")
    
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Create upload directory if not exists
    upload_dir = "uploads/submissions"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_name = f"{file_id}_{file.filename}"
    file_path = os.path.join(upload_dir, file_name)
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Create submission record
    submission = {
        "student_id": student_id,
        "id_assessment": id_assessment,
        "file_name": file.filename,
        "file_url": f"/uploads/submissions/{file_name}",
        "file_type": "pdf",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "submitted_day": datetime.now(timezone.utc).day,
        "status": "submitted"
    }
    
    # Save to database
    await db.submissions.delete_many({
        "student_id": student_id,
        "id_assessment": id_assessment
    })
    result = await db.submissions.insert_one(submission)
    submission["_id"] = str(result.inserted_id)
    
    # Update student's enrollment to mark assessment as submitted
    try:
        student_doc = await db.students.find_one({"student_id": student_id})
        enrollment_code = None
        if student_doc:
            for e in student_doc.get("enrollments", []):
                for a in e.get("assessments", []):
                    if a.get("id_assessment") == id_assessment:
                        enrollment_code = e.get("code_module")
                        break
                if enrollment_code:
                    break

        if enrollment_code is None:
            assignment_doc = await db.assignments.find_one({"id_assessment": id_assessment})
            if assignment_doc:
                enrollment_code = assignment_doc.get("code_module")

        if enrollment_code is not None:
            # Also write file metadata into the student's assessment entry so
            # client apps that re-load the `students` document see the submission
            # immediately after a reset.
            await db.students.update_one(
                {"student_id": student_id},
                {"$set": {
                    "enrollments.$[e].assessments.$[a].submitted_date": submission.get("submitted_day"),
                    "enrollments.$[e].assessments.$[a].file_url": submission.get("file_url"),
                    "enrollments.$[e].assessments.$[a].file_name": submission.get("file_name"),
                }},
                array_filters=[
                    {"e.code_module": enrollment_code},
                    {"a.id_assessment": id_assessment},
                ],
            )
    except Exception as e:
        print(f"[submit-file] failed to update student enrollment: {e}")

    # Trigger assessment reaction
    try:
        from agent.assessment_reaction import react_to_assessment_change
        summary = f"Bài nộp mới: {file.filename} cho assessment {id_assessment}"
        await react_to_assessment_change(student_id, summary, replan=True)
    except Exception as e:
        print(f"[submit-file] Reaction error: {e}")

    await log_event(
        None,
        "assignment_submitted",
        actor_id=str(student_id),
        target_id=str(id_assessment),
        payload={"filename": file.filename, "file_type": "pdf", "student_id": student_id},
        source="assignments",
    )

    return {"submission": submission}


@router.get("/{id_assessment}/submissions")
async def get_submissions(id_assessment: int, student_id: int):
    """Get all submissions for an assessment."""
    db = get_db()
    if db is not None:
        submissions = await db.submissions.find({
            "student_id": student_id,
            "id_assessment": id_assessment
        }).to_list(length=100)
        
        # Convert ObjectId to string
        for sub in submissions:
            sub["_id"] = str(sub["_id"])
        
        return {"submissions": submissions}
    
    # Mock fallback
    return {"submissions": []}


@router.get("/{id_assessment}/submission")
async def read_submission(id_assessment: int, student_id: int):
    """Return the student's submission for an assessment, if any."""
    db = get_db()
    doc = await get_submission(db, student_id, id_assessment)
    if not doc:
        return {"id_assessment": id_assessment, "submission": None}
    return {"id_assessment": id_assessment, "submission": doc}


@router.delete("/{id_assessment}/submissions/{submission_id}")
async def delete_submission(id_assessment: int, submission_id: str):
    """Delete a submission (unsubmit)."""
    db = get_db()
    if db is not None:
        try:
            oid = ObjectId(submission_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="Invalid submission id")

        sub = await db.submissions.find_one({
            "_id": oid,
            "id_assessment": id_assessment,
        })
        
        if not sub:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        # Delete file from disk
        file_url = sub.get("file_url", "")
        if file_url.startswith("/uploads/"):
            file_path = file_url.lstrip("/")
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"[delete-submission] Failed to delete file: {e}")
        
        # Delete from database
        await db.submissions.delete_one({"_id": oid})
        return {"ok": True}
    
    return {"ok": True, "mock": True}


# ── Student: Feedbacks & Comments ──────────────────────────────────────────

@router.get("/{id_assessment}/feedbacks")
async def get_feedbacks(id_assessment: int):
    """Get instructor feedbacks for an assessment."""
    db = get_db()
    if db is not None:
        feedbacks = await db.feedbacks.find({
            "assessment_id": id_assessment
        }).to_list(length=100)
        
        for fb in feedbacks:
            fb["_id"] = str(fb["_id"])
        
        return {"feedbacks": feedbacks}
    
    # Mock fallback
    return {
        "feedbacks": [
            {
                "id": 1,
                "assessment_id": id_assessment,
                "content": "Bài làm tốt, cần cải thiện phần lập luận và trình bày rõ ràng hơn.",
                "score": 7.5,
                "created_at": "2026-07-02T10:30:00",
                "instructor_name": "TS. Nguyễn Văn A"
            }
        ]
    }


@router.get("/{id_assessment}/comments")
async def get_class_comments(id_assessment: int):
    """Get all class comments for an assessment."""
    db = get_db()
    if db is not None:
        comments = await db.class_comments.find({
            "assessment_id": id_assessment
        }).sort("created_at", -1).to_list(length=100)
        
        for c in comments:
            c["_id"] = str(c["_id"])
        
        return {"comments": comments}
    
    # Mock fallback
    return {
        "comments": [
            {
                "id": 1,
                "assessment_id": id_assessment,
                "student_id": 101,
                "student_name": "Trần Thị B",
                "content": "Mọi người làm bài đến đâu rồi ạ?",
                "is_instructor": False,
                "created_at": "2026-07-03T08:00:00"
            },
            {
                "id": 2,
                "assessment_id": id_assessment,
                "student_id": 0,
                "student_name": "Giảng viên",
                "content": "Các em lưu ý deadline là 23:59 ngày mai nhé.",
                "is_instructor": True,
                "created_at": "2026-07-03T10:00:00"
            }
        ]
    }


@router.post("/{id_assessment}/comments")
async def add_class_comment(id_assessment: int, body: ClassCommentRequest):
    """Add a new class comment."""
    db = get_db()
    
    # Get student info (mock for now)
    student_name = f"Học sinh {body.student_id}"
    
    comment = {
        "id": int(datetime.now().timestamp() * 1000),
        "assessment_id": id_assessment,
        "student_id": body.student_id,
        "student_name": student_name,
        "content": body.content,
        "is_instructor": False,
        "created_at": datetime.now().isoformat()
    }
    
    if db is not None:
        result = await db.class_comments.insert_one(comment)
        comment["_id"] = str(result.inserted_id)
    else:
        comment["_id"] = "mock_id"
    
    return comment
