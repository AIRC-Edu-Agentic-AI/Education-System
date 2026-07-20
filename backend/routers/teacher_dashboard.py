from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.mongodb import db_state
from db.utils import serialize_doc

router = APIRouter()


class ImportStudentsRequest(BaseModel):
    students: List[Dict[str, Any]]


class ChatRequest(BaseModel):
    message: str


def get_db():
    db = db_state.get("db")
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    return db


@router.get("/index")
async def list_courses() -> Dict[str, Any]:
    try:
        db = get_db()
        courses = await db["processed_courses"].find({}, {"students": 0, "_id": 0}).to_list(None)
        result = []
        for course in courses:
            result.append({
                "module": course.get("module"),
                "module_name": course.get("module_name"),
                "presentation": course.get("presentation"),
                "presentation_name": course.get("presentation_name"),
                "course_length_days": int(course.get("num_weeks", 0) or 0) * 7,
                "num_weeks": course.get("num_weeks"),
                "student_count": course.get("student_count"),
            })
        return {"courses": result}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.get("/course/{module}/{presentation}/classes")
async def get_course_classes(module: str, presentation: str) -> Dict[str, Any]:
    try:
        db = get_db()
        course = await db["courses"].find_one(
            {"course_code": module, "presentation": presentation},
            {"_id": 0, "classes": 1}
        )
        if not course:
            return {"classes": []}
            
        return {"classes": course.get("classes", [])}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc

@router.get("/course/{module}/{presentation}/students-lite")
async def get_course_students_lite(module: str, presentation: str) -> Dict[str, Any]:
    try:
        db = get_db()
        students = await db["processed_students"].find(
            {"code_module": module, "code_presentation": presentation},
            {"_id": 0, "id_student": 1, "name": 1}
        ).to_list(None)
        return {"students": students}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc

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
        return serialize_doc({**course, "students": students})
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


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
        return serialize_doc(student)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="student_id must be an integer") from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.post("/students/import")
async def import_students(payload: ImportStudentsRequest) -> Dict[str, Any]:
    try:
        db = get_db()
        result = await db["students"].insert_many(payload.students)
        return {"message": "Imported successfully", "count": len(result.inserted_ids)}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.get("/attendance-stats/{module}/{presentation}")
async def attendance_stats(module: str, presentation: str) -> List[Dict[str, Any]]:
    try:
        db = get_db()
        raw_data = await db["processed_students"].aggregate([
            {"$match": {"code_module": module, "code_presentation": presentation}},
            {"$group": {"_id": "$final_result", "count": {"$sum": 1}}},
        ]).to_list(None)

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
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.post("/ai/chat")
async def ai_chat(payload: ChatRequest) -> Dict[str, str]:
    return {"reply": f"ÄÃ£ nháº­n cÃ¢u há»i: {payload.message}"}


@router.get("/classrooms")
async def get_classrooms(module: str, presentation: str) -> Dict[str, Any]:
    """Get classrooms dynamically by chunking students if not explicitly defined."""
    try:
        db = get_db()
        import json as _json
        
        # 1. Check if explicit classrooms exist
        docs = await db["classrooms"].find(
            {"module": module, "code_presentation": presentation, "status": {"$ne": "deleted"}},
            {"_id": 0, "name": 1, "student_ids": 1}
        ).to_list(None)
        
        classrooms = []
        for d in docs:
            sids = d.get("student_ids", [])
            if isinstance(sids, str):
                try:
                    sids = _json.loads(sids)
                except Exception:
                    sids = []
            classrooms.append({"class_name": d.get("name", ""), "members": sids})
            
        # 2. If no classrooms exist, dynamically chunk students of this module+presentation
        if not classrooms:
            students = await db["processed_students"].find(
                {"code_module": module, "code_presentation": presentation},
                {"_id": 0, "id_student": 1}
            ).to_list(None)
            
            sids = [s["id_student"] for s in students if "id_student" in s]
            
            # Chunk into groups of ~120 students
            chunk_size = 120
            for i in range(0, len(sids), chunk_size):
                chunk = sids[i:i+chunk_size]
                class_num = (i // chunk_size) + 1
                classrooms.append({
                    "class_name": f"Nhóm {class_num}",
                    "members": chunk
                })
        
        return {"classes": classrooms}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc

@router.get("/course-options")
async def get_course_options() -> Dict[str, Any]:
    """Get all unique module and presentation options from processed_students"""
    try:
        db = get_db()
        pipeline = [
            {"$group": {"_id": {"module": "$code_module", "pres": "$code_presentation"}, "count": {"$sum": 1}}},
            {"$sort": {"_id.module": 1, "_id.pres": 1}}
        ]
        results = await db["processed_students"].aggregate(pipeline).to_list(None)
        
        options = []
        for r in results:
            options.append({
                "module": r["_id"]["module"],
                "presentation": r["_id"]["pres"],
                "student_count": r["count"]
            })
        return {"options": options}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc

@router.get("/course-students")
async def get_course_students(module: str, presentation: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get all students for a course."""
    try:
        db = get_db()
        query = {"code_module": module}
        if presentation and presentation != "ALL":
            query["code_presentation"] = presentation
        
        students = await db["processed_students"].find(
            query,
            {"_id": 0, "id_student": 1, "region": 1}
        ).to_list(None)
        
        return students
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc
