from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from db.mongodb import get_db
from db.mock_data import MOCK_MILESTONES
from db.submissions import get_submission, submit_assignment

router = APIRouter()


class MilestoneUpdateRequest(BaseModel):
    student_id: int
    id_assessment: int
    milestone_id: str
    status: str


class SubmitAssignmentRequest(BaseModel):
    student_id: int
    content: str = Field(..., min_length=1, max_length=8000)


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


@router.get("/{id_assessment}/submission")
async def read_submission(id_assessment: int, student_id: int):
    """Return the student's submission for an assessment, if any."""
    db = get_db()
    doc = await get_submission(db, student_id, id_assessment)
    if not doc:
        return {"id_assessment": id_assessment, "submission": None}
    return {"id_assessment": id_assessment, "submission": doc}


@router.post("/{id_assessment}/submit")
async def submit(id_assessment: int, body: SubmitAssignmentRequest):
    """Submit assignment work (text or link). Marks assessment as submitted."""
    db = get_db()
    try:
        submission = await submit_assignment(
            db, body.student_id, id_assessment, body.content
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"ok": True, "submission": submission}
