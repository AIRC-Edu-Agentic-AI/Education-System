from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from db.mongodb import db_state

router = APIRouter()

class ImportStudentsRequest(BaseModel):
    students: List[Dict[str, Any]]

class ChatRequest(BaseModel):
    message: str

def get_db() -> AsyncIOMotorDatabase:
    if not db_state.get("db"):
        raise HTTPException(status_code=503, detail="Database not connected")
    return db_state["db"]

@router.get("/index")
async def list_courses() -> Dict[str, Any]:
    try:
        db = get_db()
        courses = await db["processed_courses"].find({}, {"students": 0, "_id": 0}).to_list(None)
        result = []
        for course in courses:
            result.append(
                {
                    "module": course.get("module"),
                    "module_name": course.get("module_name"),
                    "presentation": course.get("presentation"),
                    "presentation_name": course.get("presentation_name"),
                    "course_length_days": int(course.get("num_weeks", 0) or 0) * 7,
                    "num_weeks": course.get("num_weeks"),
                    "student_count": course.get("student_count"),
                }
            )
        return {"courses": result}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc

@router.get("/course/{module}/{presentation}")
async def get_course(module: str, presentation: str) -> Dict[str, Any]:
    try:
        db = get_db()
        course = await db["processed_courses"].find_one({"module": module, "presentation": presentation}, {"_id": 0})
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
            {"code_module": module, "code_presentation": presentation, "id_student": int(student_id)},
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
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc

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
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc

@router.post("/ai/chat")
async def ai_chat(payload: ChatRequest) -> Dict[str, str]:
    reply = f"Tôi đã nhận câu hỏi: {payload.message}. Bạn có thể mở rộng logic này bằng model LLM trong bước tiếp theo."
    return {"reply": reply}
