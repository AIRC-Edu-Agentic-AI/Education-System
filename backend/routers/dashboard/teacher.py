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
    db = db_state.get("db")
    if db is None or not db_state.get("connected", False):
        raise HTTPException(status_code=503, detail="Database not connected")
    return db


def _course_payload(course: Dict[str, Any]) -> Dict[str, Any]:
    module = course.get("module") or course.get("code_module") or course.get("module_code")
    presentation = course.get("presentation") or course.get("code_presentation") or course.get("presentation_code")
    return {
        "module": module,
        "module_name": course.get("module_name") or course.get("title") or module,
        "presentation": presentation,
        "presentation_name": course.get("presentation_name") or course.get("term") or presentation,
        "course_length_days": int(course.get("num_weeks", 0) or course.get("course_length_days", 0) or 0) * 7,
        "num_weeks": course.get("num_weeks") or course.get("weeks") or 15,
        "student_count": course.get("student_count") or course.get("num_students") or 0,
    }


def _student_payload(student: Dict[str, Any]) -> Dict[str, Any]:
    return {
        **student,
        "id_student": student.get("id_student") or student.get("student_id"),
        "code_module": student.get("code_module") or student.get("module") or student.get("module_code"),
        "code_presentation": student.get("code_presentation") or student.get("presentation") or student.get("presentation_code"),
        "name": student.get("name") or student.get("full_name") or student.get("student_name") or f"Student {student.get('id_student') or student.get('student_id')}",
    }


async def _find_collection(db, candidates: List[str]):
    for name in candidates:
        try:
            if name in await db.list_collection_names():
                return name
        except Exception:
            continue
    return None


# ── Courses ──────────────────────────────────────────────────────────────────

@router.get("/index")
async def list_courses() -> Dict[str, Any]:
    try:
        db = get_db()
        course_collection = await _find_collection(db, ["processed_courses", "courses", "course"])
        if not course_collection:
            return {"courses": []}
        courses = await db[course_collection].find({}, {"students": 0, "_id": 0}).to_list(None)
        result = [_course_payload(c) for c in courses]
        return {"courses": result}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc


@router.get("/course/{module}/{presentation}")
async def get_course(module: str, presentation: str) -> Dict[str, Any]:
    try:
        db = get_db()
        course_collection = await _find_collection(db, ["processed_courses", "courses", "course"])
        student_collection = await _find_collection(db, ["processed_students", "students", "student"])
        course = None
        if course_collection:
            course = await db[course_collection].find_one(
                {
                    "$or": [
                        {"module": module, "presentation": presentation},
                        {"code_module": module, "code_presentation": presentation},
                    ]
                },
                {"_id": 0},
            )
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        students = []
        if student_collection:
            students = await db[student_collection].find(
                {
                    "$or": [
                        {"code_module": module, "code_presentation": presentation},
                        {"module": module, "presentation": presentation},
                    ]
                },
                {"_id": 0},
            ).to_list(None)
        return {**_course_payload(course), "students": [_student_payload(student) for student in students]}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc


@router.get("/student/{module}/{presentation}/{student_id}")
async def get_student(module: str, presentation: str, student_id: str) -> Dict[str, Any]:
    try:
        db = get_db()
        student_collection = await _find_collection(db, ["processed_students", "students", "student"])
        student = None
        if student_collection:
            student = await db[student_collection].find_one(
                {
                    "$or": [
                        {
                            "code_module": module,
                            "code_presentation": presentation,
                            "id_student": int(student_id),
                        },
                        {
                            "module": module,
                            "presentation": presentation,
                            "student_id": int(student_id),
                        },
                    ]
                },
                {"_id": 0},
            )
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        return _student_payload(student)
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
        student_collection = await _find_collection(db, ["processed_students", "students", "student"])
        if not student_collection:
            return []
        raw_data = await db[student_collection].aggregate(
            [
                {
                    "$match": {
                        "$or": [
                            {"code_module": module, "code_presentation": presentation},
                            {"module": module, "presentation": presentation},
                        ]
                    }
                },
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
