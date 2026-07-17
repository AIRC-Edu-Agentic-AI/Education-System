from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from db.mongodb import db_state

router = APIRouter()

DEMO_COURSES = [
    {
        "module": "COMP101",
        "module_name": "Programming Fundamentals",
        "presentation": "2024A",
        "presentation_name": "Spring 2024",
        "num_weeks": 15,
        "student_count": 24,
    },
    {
        "module": "MATH102",
        "module_name": "Linear Algebra",
        "presentation": "2024A",
        "presentation_name": "Spring 2024",
        "num_weeks": 15,
        "student_count": 19,
    },
    {
        "module": "DATA201",
        "module_name": "Data Analysis",
        "presentation": "2024A",
        "presentation_name": "Spring 2024",
        "num_weeks": 15,
        "student_count": 21,
    },
]

DEMO_STUDENTS = [
    {
        "id_student": 1001,
        "name": "An Nguyen",
        "gender": "M",
        "region": "Hanoi",
        "highest_education": "Bachelor",
        "imd_band": "20-30%",
        "age_band": "18-21",
        "num_of_prev_attempts": 0,
        "studied_credits": 60,
        "disability": False,
        "final_result": "Pass",
        "date_registration": 1,
        "date_unregistration": None,
        "weekly_clicks": [120, 140, 150, 130, 110, 90, 80],
        "decayed_engagement": [0.8, 0.75, 0.72, 0.7, 0.68, 0.65, 0.6],
        "assessments": [
            {"id_assessment": 1, "assessment_type": "TMA", "date_due": 10, "weight": 20, "score": 78, "date_submitted": 8},
            {"id_assessment": 2, "assessment_type": "CMA", "date_due": 20, "weight": 30, "score": 82, "date_submitted": 19},
        ],
        "risk_by_week": [0.3, 0.35, 0.4, 0.42, 0.44, 0.48, 0.5],
        "tier_by_week": [1, 1, 2, 2, 2, 2, 2],
        "lstm_trajectories": {"w05": [0.4], "w10": [0.45], "w15": [0.5], "w20": [0.55], "w25": [0.6]},
        "code_module": "COMP101",
        "code_presentation": "2024A",
    },
    {
        "id_student": 1002,
        "name": "Lan Tran",
        "gender": "F",
        "region": "Da Nang",
        "highest_education": "Bachelor",
        "imd_band": "10-20%",
        "age_band": "18-21",
        "num_of_prev_attempts": 1,
        "studied_credits": 45,
        "disability": False,
        "final_result": "Fail",
        "date_registration": 2,
        "date_unregistration": None,
        "weekly_clicks": [90, 100, 110, 80, 70, 50, 40],
        "decayed_engagement": [0.7, 0.69, 0.66, 0.62, 0.58, 0.53, 0.5],
        "assessments": [
            {"id_assessment": 3, "assessment_type": "TMA", "date_due": 12, "weight": 20, "score": 55, "date_submitted": 10},
            {"id_assessment": 4, "assessment_type": "Exam", "date_due": 22, "weight": 60, "score": 48, "date_submitted": 21},
        ],
        "risk_by_week": [0.4, 0.48, 0.6, 0.68, 0.74, 0.78, 0.82],
        "tier_by_week": [2, 2, 3, 3, 3, 3, 3],
        "lstm_trajectories": {"w05": [0.3], "w10": [0.4], "w15": [0.5], "w20": [0.6], "w25": [0.7]},
        "code_module": "COMP101",
        "code_presentation": "2024A",
    },
    {
        "id_student": 1003,
        "name": "Minh Le",
        "gender": "M",
        "region": "Ho Chi Minh",
        "highest_education": "Bachelor",
        "imd_band": "30-40%",
        "age_band": "18-21",
        "num_of_prev_attempts": 0,
        "studied_credits": 50,
        "disability": False,
        "final_result": "Distinction",
        "date_registration": 3,
        "date_unregistration": None,
        "weekly_clicks": [160, 170, 180, 175, 160, 150, 140],
        "decayed_engagement": [0.9, 0.88, 0.86, 0.84, 0.82, 0.8, 0.78],
        "assessments": [
            {"id_assessment": 5, "assessment_type": "TMA", "date_due": 9, "weight": 25, "score": 90, "date_submitted": 7},
            {"id_assessment": 6, "assessment_type": "Exam", "date_due": 21, "weight": 75, "score": 88, "date_submitted": 20},
        ],
        "risk_by_week": [0.2, 0.22, 0.25, 0.24, 0.23, 0.22, 0.21],
        "tier_by_week": [1, 1, 1, 1, 1, 1, 1],
        "lstm_trajectories": {"w05": [0.5], "w10": [0.6], "w15": [0.7], "w20": [0.75], "w25": [0.8]},
        "code_module": "DATA201",
        "code_presentation": "2024A",
    },
]

DEMO_ATTENDANCE = [
    {"name": "Pass", "value": 16, "color": "#4CAF50"},
    {"name": "Fail", "value": 4, "color": "#F44336"},
    {"name": "Withdrawn", "value": 2, "color": "#FFC107"},
]

class ImportStudentsRequest(BaseModel):
    students: List[Dict[str, Any]]

class ChatRequest(BaseModel):
    message: str

def get_db() -> AsyncIOMotorDatabase:
    db = db_state.get("db")
    # Tạm thời bỏ điều kiện kiểm tra db_state["connected"] quá khắt khe
    if db is None:
        print("❌ LỖI NGHIÊM TRỌNG: Backend chưa nhận được biến kết nối MongoDB!")
        raise HTTPException(status_code=503, detail="Database not connected")
    return db


def _course_payload(course: Dict[str, Any]) -> Dict[str, Any]:
    module = (
        course.get("module")
        or course.get("code_module")
        or course.get("module_code")
        or course.get("course_code")
    )
    presentation = (
        course.get("presentation")
        or course.get("code_presentation")
        or course.get("presentation_code")
        or course.get("term")
    )
    student_count = course.get("student_count") or course.get("num_students")
    if student_count in (None, "", []):
        members = course.get("members")
        if isinstance(members, list):
            student_count = len(members)
        else:
            student_count = 0

    return {
        "module": module,
        "module_name": course.get("module_name") or course.get("title") or module,
        "presentation": presentation,
        "presentation_name": course.get("presentation_name") or course.get("term") or presentation,
        "course_length_days": int(course.get("num_weeks", 0) or course.get("course_length_days", 0) or 0) * 7,
        "num_weeks": course.get("num_weeks") or course.get("weeks") or 15,
        "student_count": student_count,
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
    try:
        existing = await db.list_collection_names()
    except Exception:
        return None
    for name in candidates:
        if name in existing:
            return name
    return None


@router.get("/index")
async def list_courses() -> Dict[str, Any]:
    try:
        db = get_db()
        course_collection = await _find_collection(db, ["processed_courses", "courses", "course"])
        if not course_collection:
            return {"courses": DEMO_COURSES}
        courses = await db[course_collection].find({}, {"students": 0, "_id": 0}).to_list(None)
        if courses:
            result = [_course_payload(course) for course in courses]
            return {"courses": result}
        return {"courses": DEMO_COURSES}
    except Exception:
        return {"courses": DEMO_COURSES}

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
                        {"course_code": module, "presentation": presentation},
                        {"module": module, "presentation": presentation},
                        {"code_module": module, "code_presentation": presentation},
                    ]
                },
                {"_id": 0},
            )
        if course:
            students = []
            if student_collection:
                students = await db[student_collection].find(
                    {
                        "$or": [
                            {"code_module": module, "code_presentation": presentation},
                            {"module": module, "presentation": presentation},
                            {"course_code": module, "presentation": presentation},
                        ]
                    },
                    {"_id": 0},
                ).to_list(None)
            return {**_course_payload(course), "students": [_student_payload(student) for student in students]}

        demo_course = next((c for c in DEMO_COURSES if c["module"] == module and c["presentation"] == presentation), None)
        if demo_course:
            students = [student for student in DEMO_STUDENTS if student["code_module"] == module and student["code_presentation"] == presentation]
            return {**demo_course, "students": students, "cohort_p75_decayed": [0.6, 0.65, 0.7, 0.72, 0.74, 0.76, 0.78]}

        raise HTTPException(status_code=404, detail="Course not found")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable")

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
                        {"code_module": module, "code_presentation": presentation, "id_student": int(student_id)},
                        {"module": module, "presentation": presentation, "student_id": int(student_id)},
                    ]
                },
                {"_id": 0},
            )
        if student:
            return _student_payload(student)

        demo_student = next(
            (s for s in DEMO_STUDENTS if s["code_module"] == module and s["code_presentation"] == presentation and s["id_student"] == int(student_id)),
            None,
        )
        if demo_student:
            return demo_student

        raise HTTPException(status_code=404, detail="Student not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="student_id must be an integer") from exc
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable")

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

        if raw_data:
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

        return DEMO_ATTENDANCE
    except Exception:
        return DEMO_ATTENDANCE

@router.post("/ai/chat")
async def ai_chat(payload: ChatRequest) -> Dict[str, str]:
    reply = f"Tôi đã nhận câu hỏi: {payload.message}. Bạn có thể mở rộng logic này bằng model LLM trong bước tiếp theo."
    return {"reply": reply}
