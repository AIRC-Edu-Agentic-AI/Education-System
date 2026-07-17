# ── dashboard/teacher.py ──────────────────────────────────────────────────────
# Dashboard lớp học, thống kê, Risk — Teacher view
from typing import Any, Dict, List

from bson import ObjectId
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.mongodb import db_state

router = APIRouter()


class ImportStudentsRequest(BaseModel):
    students: List[Dict[str, Any]]


def get_db():
    if not db_state.get("db"):
        raise HTTPException(status_code=503, detail="Database not connected")
    return db_state["db"]


# ── Courses ──────────────────────────────────────────────────────────────────

@router.get("/index")
async def list_courses() -> Dict[str, Any]:
    try:
        db = get_db()
        courses = await db["processed_courses"].find(
            {}, {"students": 0, "_id": 0}
        ).to_list(None)
        result = [
            {
                "module": c.get("module"),
                "module_name": c.get("module_name"),
                "presentation": c.get("presentation"),
                "presentation_name": c.get("presentation_name"),
                "course_length_days": int(c.get("num_weeks", 0) or 0) * 7,
                "num_weeks": c.get("num_weeks"),
                "student_count": c.get("student_count"),
            }
            for c in courses
        ]
        return {"courses": result}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc


@router.get("/course/{module}/{presentation}")
async def get_course(module: str, presentation: str) -> Dict[str, Any]:
    try:
        db = get_db()
        course = await db["processed_courses"].find_one(
            {"module": module, "presentation": presentation}, {"_id": 0}
        )
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        students = await db["processed_students"].find(
            {"code_module": module, "code_presentation": presentation},
            {"_id": 0},
        ).to_list(None)
        return {**course, "students": students}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc


@router.get("/student/{module}/{presentation}/{student_id}")
async def get_student(module: str, presentation: str, student_id: str) -> Dict[str, Any]:
    try:
        db = get_db()
        student = await db["processed_students"].find_one(
            {
                "code_module": module,
                "code_presentation": presentation,
                "id_student": int(student_id),
            },
            {"_id": 0},
        )
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        return student
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="student_id must be an integer") from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc


@router.post("/students/import")
async def import_students(payload: ImportStudentsRequest) -> Dict[str, Any]:
    try:
        db = get_db()
        result = await db["students"].insert_many(payload.students)
        return {"message": "Imported successfully", "count": len(result.inserted_ids)}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc


# ── Attendance Statistics ─────────────────────────────────────────────────────

@router.get("/attendance-stats/{module}/{presentation}")
async def attendance_stats(module: str, presentation: str) -> List[Dict[str, Any]]:
    try:
        db = get_db()
        raw_data = await db["processed_students"].aggregate(
            [
                {"$match": {"code_module": module, "code_presentation": presentation}},
                {"$group": {"_id": "$final_result", "count": {"$sum": 1}}},
            ]
        ).to_list(None)

        color_map = {
            "Pass": "#4CAF50",
            "Fail": "#F44336",
            "Withdrawn": "#FFC107",
            "Distinction": "#2196F3",
        }
        return [
            {
                "name": item.get("_id") or "Unknown",
                "value": item.get("count", 0),
                "color": color_map.get(item.get("_id"), "#9E9E9E"),
            }
            for item in raw_data
        ]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
