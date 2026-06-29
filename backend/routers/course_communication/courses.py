"""Course endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.mongodb import get_db
from db.course_communication import (
    enroll_student_in_course,
    get_course,
    get_student_courses,
    withdraw_student_from_course,
)

router = APIRouter()


class CourseEnrollmentRequest(BaseModel):
    course_code: str
    title: str
    code_presentation: str | None = ""
    term: str | None = "2024A"
    instructor_ids: list[int] | None = None
    class_rep_ids: list[int] | None = None


@router.get("/student/{student_id}")
async def list_student_courses(student_id: int):
    """List all courses for a student."""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database required")
    courses = await get_student_courses(db, student_id)
    return courses


@router.post("/student/{student_id}")
async def enroll_course(student_id: int, body: CourseEnrollmentRequest):
    """Enroll a student in a course."""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database required")
    course = await enroll_student_in_course(
        db,
        student_id,
        body.course_code,
        body.title,
        body.code_presentation or "",
        body.term or "2024A",
        body.instructor_ids,
        body.class_rep_ids,
    )
    if course is None:
        raise HTTPException(status_code=500, detail="Failed to enroll student")
    return course


@router.delete("/student/{student_id}/{course_code}")
async def withdraw_course(student_id: int, course_code: str):
    """Withdraw a student from a course."""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database required")
    success = await withdraw_student_from_course(db, student_id, course_code)
    if not success:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    return {"ok": True}


@router.get("/{course_code}")
async def get_course_info(course_code: str):
    """Get course information."""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database required")
    course = await get_course(db, course_code)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course
