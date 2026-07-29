from typing import Any, Dict, List, Optional
from bson import ObjectId

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
        courses = await db["courses"].find({}, {"_id": 0}).to_list(None)
        result = []
        for course in courses:
            try:
                mod_len = int(course.get("module_length") or 30)
            except (ValueError, TypeError):
                mod_len = 30
            result.append({
                "module": course.get("code_module"),
                "module_name": course.get("title", ""),
                "presentation": course.get("code_presentation"),
                "presentation_name": course.get("code_presentation"),
                "course_length_days": mod_len * 7,
                "num_weeks": mod_len,
                "student_count": 0,
            })
        return {"courses": result}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.get("/course/{module}/{presentation}/classes")
async def get_course_classes(module: str, presentation: str) -> Dict[str, Any]:
    try:
        db = get_db()
        classrooms = await db["classrooms"].find(
            {"course_code": module},
            {"_id": 0, "name": 1, "student_ids": 1}
        ).to_list(None)
        return {"classes": classrooms}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.get("/course/{module}/{presentation}/students-lite")
async def get_course_students_lite(module: str, presentation: str) -> Dict[str, Any]:
    try:
        db = get_db()
        students = await db["students"].find(
            {"enrollments": {"$elemMatch": {"code_module": module, "code_presentation": presentation}}},
            {"_id": 0, "student_id": 1, "full_name": 1}
        ).to_list(None)
        
        mapped = []
        for s in students:
            mapped.append({
                "id_student": s.get("student_id"),
                "name": s.get("full_name")
            })
        return {"students": mapped}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.get("/course/{module}/{presentation}")
async def get_course(module: str, presentation: str) -> Dict[str, Any]:
    try:
        db = get_db()
        course = await db["courses"].find_one(
            {"code_module": module, "code_presentation": presentation}, {"_id": 0}
        )
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        course_data = {
            "module": course.get("code_module"),
            "presentation": course.get("code_presentation"),
            "module_name": course.get("title"),
            "num_weeks": course.get("module_length", 30),
            "cohort_p75_decayed": [0] * 40
        }

        students_raw = await db["students"].find(
            {"enrollments": {"$elemMatch": {"code_module": module, "code_presentation": presentation}}},
            {"_id": 0},
        ).to_list(None)
        
        students = []
        for s in students_raw:
            students.append({
                "id_student": s.get("student_id"),
                "name": s.get("full_name"),
                "gender": s.get("demographics", {}).get("gender", "Unknown"),
                "region": s.get("demographics", {}).get("region", "Unknown"),
                "highest_education": s.get("demographics", {}).get("highest_education", "Unknown"),
                "age_band": s.get("demographics", {}).get("age_band", "Unknown"),
                "num_of_prev_attempts": s.get("demographics", {}).get("num_of_prev_attempts", 0),
                "studied_credits": s.get("demographics", {}).get("studied_credits", 0),
                "disability": "Y" if s.get("demographics", {}).get("disability") else "N",
                "final_result": "Unknown",
                "date_registration": 0,
                "date_unregistration": None,
                "weekly_clicks": [0] * 40,
                "decayed_engagement": [0] * 40,
                "risk_by_week": [0.2] * 40,
                "tier_by_week": [1] * 40,
                "lstm_trajectories": None,
                "assessments": []
            })

        return serialize_doc({**course_data, "students": students})
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.get("/student/{module}/{presentation}/{student_id}")
async def get_student(module: str, presentation: str, student_id: str) -> Dict[str, Any]:
    try:
        db = get_db()
        student = await db["students"].find_one(
            {"student_id": int(student_id)},
            {"_id": 0},
        )
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
            
        mapped_student = {
            "id_student": student.get("student_id"),
            "name": student.get("full_name"),
            "code_module": module,
            "code_presentation": presentation,
            "gender": student.get("demographics", {}).get("gender", "Unknown"),
            "region": student.get("demographics", {}).get("region", "Unknown"),
            "highest_education": student.get("demographics", {}).get("highest_education", "Unknown"),
            "age_band": student.get("demographics", {}).get("age_band", "Unknown"),
            "num_of_prev_attempts": student.get("demographics", {}).get("num_of_prev_attempts", 0),
            "studied_credits": student.get("demographics", {}).get("studied_credits", 0),
            "disability": "Y" if student.get("demographics", {}).get("disability") else "N",
            "final_result": "Unknown",
            "date_registration": 0,
            "date_unregistration": None,
            "weekly_clicks": [0] * 40,
            "decayed_engagement": [0] * 40,
            "risk_by_week": [0.2] * 40,
            "tier_by_week": [1] * 40,
            "lstm_trajectories": None,
            "assessments": []
        }
        return serialize_doc(mapped_student)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.post("/students/import")
async def import_students(payload: ImportStudentsRequest) -> Dict[str, Any]:
    try:
        db = get_db()
        result = await db["students"].insert_many(payload.students)
        return {"message": "Imported successfully", "count": len(result.inserted_ids)}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.get("/attendance-stats/{module}/{presentation}")
async def attendance_stats(module: str, presentation: str) -> List[Dict[str, Any]]:
    try:
        db = get_db()
        pipeline = [
            {"$match": {
                "enrollments": {"$elemMatch": {"code_module": module, "code_presentation": presentation}}
            }},
            {"$unwind": "$enrollments"},
            {"$match": {
                "enrollments.code_module": module,
                "enrollments.code_presentation": presentation
            }},
            {"$group": {
                "_id": "$enrollments.final_result",
                "count": {"$sum": 1}
            }}
        ]
        results = await db["students"].aggregate(pipeline).to_list(None)
        
        stats_map = {
            "Pass": {"value": 0, "color": "#4CAF50"},
            "Fail": {"value": 0, "color": "#F44336"},
            "Withdrawn": {"value": 0, "color": "#FFC107"},
            "Distinction": {"value": 0, "color": "#2196F3"},
        }
        
        for r in results:
            name = r.get("_id")
            count = r.get("count", 0)
            
            if not name:
                # Distribute 'Unknown' into demo categories (75% On Time, 15% Late, 10% Absent)
                pass_c = int(count * 0.75)
                fail_c = int(count * 0.15)
                withdrawn_c = count - pass_c - fail_c
                
                stats_map["Pass"]["value"] += pass_c
                stats_map["Fail"]["value"] += fail_c
                stats_map["Withdrawn"]["value"] += withdrawn_c
            else:
                if name in stats_map:
                    stats_map[name]["value"] += count
                else:
                    stats_map[name] = {"value": count, "color": "#9E9E9E"}
                
        output = []
        for name, data in stats_map.items():
            if data["value"] > 0:
                output.append({"name": name, "value": data["value"], "color": data["color"]})
                
        if not output:
            return [{"name": "No Data", "value": 1, "color": "#E0E0E0"}]
            
        return output
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.post("/ai/chat")
async def ai_chat(payload: ChatRequest) -> Dict[str, str]:
    return {"reply": f"Đã nhận câu hỏi: {payload.message}"}


@router.get("/classrooms")
async def get_classrooms(module: str, presentation: str) -> Dict[str, Any]:
    try:
        db = get_db()
        docs = await db["classrooms"].find(
            {"course_code": module},
            {"_id": 0, "name": 1, "student_ids": 1}
        ).to_list(None)
        
        classrooms = []
        for d in docs:
            classrooms.append({"class_name": d.get("name", ""), "members": d.get("student_ids", [])})
            
        return {"classes": classrooms}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.get("/course-options")
async def get_course_options() -> Dict[str, Any]:
    try:
        db = get_db()
        courses = await db["courses"].find({}, {"_id": 0}).to_list(None)
        
        options = []
        for r in courses:
            options.append({
                "module": r.get("code_module"),
                "presentation": r.get("code_presentation"),
                "student_count": 0
            })
        return {"options": options}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.get("/course-students")
async def get_course_students(module: str, presentation: Optional[str] = None) -> List[Dict[str, Any]]:
    try:
        db = get_db()
        query = {"enrollments.code_module": module}
        if presentation:
            query = {"enrollments": {"$elemMatch": {"code_module": module, "code_presentation": presentation}}}
            
        students = await db["students"].find(
            query,
            {"_id": 0, "student_id": 1, "demographics.region": 1}
        ).to_list(None)
        
        mapped = []
        for s in students:
            mapped.append({
                "id_student": s.get("student_id"),
                "region": s.get("demographics", {}).get("region", "Unknown")
            })
        return mapped
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc
