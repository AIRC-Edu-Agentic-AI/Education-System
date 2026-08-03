from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional, List
import shutil
import os
from datetime import datetime
import uuid

from db.mongodb import get_db
from db.mock_data import MOCK_MILESTONES
from db.submissions import get_submission, submit_assignment

router = APIRouter()

# ── Models ──────────────────────────────────────────────────────
class MilestoneUpdateRequest(BaseModel):
    student_id: int
    id_assessment: int
    milestone_id: str
    status: str


class SubmitAssignmentRequest(BaseModel):
    student_id: int
    content: str = Field(..., min_length=1, max_length=8000)

class ClassCommentRequest(BaseModel):
    student_id: int
    content: str = Field(..., min_length=1, max_length=1000)

# ── Existing endpoints ────────────────────────────────────────
@router.get("/{id_assessment}/milestones")
async def get_milestones(id_assessment: int, student_id: int):
    """Return milestone list for an assessment. Empty list if none generated yet."""
    db = get_db()
    if db is not None:
        doc = await db.assignment_milestones.find_one(
            {"student_id": student_id, "id_assessment": id_assessment}
        )
        if doc:
            doc["_id"] = str(doc["_id"])
            return doc
        return {"id_assessment": id_assessment, "milestones": []}
    # Mock fallback
    for m in MOCK_MILESTONES:
        if m["id_assessment"] == id_assessment and m["student_id"] == student_id:
            return {k: v for k, v in m.items() if k != "_id"}
    return {"id_assessment": id_assessment, "milestones": []}


@router.post("/{id_assessment}/breakdown")
async def trigger_breakdown(id_assessment: int, student_id: int):
    """Trigger milestone generation. Returns existing milestones if already done."""
    db = get_db()
    # Return existing if already generated
    if db is not None:
        existing = await db.assignment_milestones.find_one(
            {"student_id": student_id, "id_assessment": id_assessment}
        )
        if existing:
            existing["_id"] = str(existing["_id"])
            return existing
    else:
        for m in MOCK_MILESTONES:
            if m["id_assessment"] == id_assessment and m["student_id"] == student_id:
                return {k: v for k, v in m.items() if k != "_id"}

    # Generate via agent
    from agent.assignment_breakdown import run_breakdown
    await run_breakdown(student_id, id_assessment)

    # Return newly created milestones
    if db is not None:
        doc = await db.assignment_milestones.find_one(
            {"student_id": student_id, "id_assessment": id_assessment}
        )
        if doc:
            doc["_id"] = str(doc["_id"])
            return doc
    return {"id_assessment": id_assessment, "milestones": [], "status": "processing"}


@router.patch("/milestone/status")
async def update_milestone_status(body: MilestoneUpdateRequest):
    """Update a single milestone status."""
    db = get_db()
    if db is None:
        return {"ok": True, "mock": True}
    await db.assignment_milestones.update_one(
        {
            "student_id": body.student_id,
            "id_assessment": body.id_assessment,
            "milestones.id": body.milestone_id,
        },
        {"$set": {"milestones.$.status": body.status}},
    )
    return {"ok": True}

# ── NEW: Submission with file ──────────────────────────────
@router.post("/{id_assessment}/submit-file")
async def submit_assignment_file(
    id_assessment: int,
    student_id: int = Form(...),
    file: UploadFile = File(...)
):
    """Submit assignment with PDF file."""
    db = get_db()
    
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
        "id": int(datetime.now().timestamp() * 1000),
        "student_id": student_id,
        "id_assessment": id_assessment,
        "file_name": file.filename,
        "file_url": f"/uploads/submissions/{file_name}",
        "file_type": "pdf",
        "submitted_at": datetime.now().isoformat(),
        "submitted_day": datetime.now().day,
        "status": "submitted"
    }
    
    # Save to database
    if db is not None:
        # Remove old submission if exists
        await db.submissions.delete_many({
            "student_id": student_id,
            "id_assessment": id_assessment
        })
        await db.submissions.insert_one(submission)
        submission["_id"] = str(submission["_id"])
    
    # Trigger assessment reaction
    try:
        from agent.assessment_reaction import react_to_assessment_change
        summary = f"Bài nộp mới: {file.filename} cho assessment {id_assessment}"
        await react_to_assessment_change(student_id, summary, replan=True)
    except Exception as e:
        print(f"[submit-file] Reaction error: {e}")
    
    return {"submission": submission}

# ── NEW: Get all submissions ────────────────────────────────
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

# ── NEW: Get single submission (existing) ───────────────────
@router.get("/{id_assessment}/submission")
async def read_submission(id_assessment: int, student_id: int):
    """Return the student's submission for an assessment, if any."""
    db = get_db()
    doc = await get_submission(db, student_id, id_assessment)
    if not doc:
        return {"id_assessment": id_assessment, "submission": None}
    return {"id_assessment": id_assessment, "submission": doc}

# ── NEW: Delete submission (Unsubmit) ───────────────────────
@router.delete("/{id_assessment}/submissions/{submission_id}")
async def delete_submission(id_assessment: int, submission_id: int):
    """Delete a submission (unsubmit)."""
    db = get_db()
    if db is not None:
        # Find the submission to get file path
        sub = await db.submissions.find_one({
            "id": submission_id,
            "id_assessment": id_assessment
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
        await db.submissions.delete_one({"id": submission_id})
        return {"ok": True}
    
    return {"ok": True, "mock": True}

# ── NEW: Get instructor feedbacks ────────────────────────────
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

# ── NEW: Get class comments ──────────────────────────────────
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

# ── NEW: Add class comment ──────────────────────────────────
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