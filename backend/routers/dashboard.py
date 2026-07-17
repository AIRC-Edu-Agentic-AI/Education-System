from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from db.mongodb import db_state

router = APIRouter()


class ImportStudentsRequest(BaseModel):
    students: List[Dict[str, Any]]


class ChatRequest(BaseModel):
    message: str


class NotificationPayload(BaseModel):
    senderRole: str
    receiverRole: str
    type: str
    title: str
    content: str
    student_ids: Optional[List[int]] = None  # nếu có → ghi schema student app


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


@router.get("/notifications")
async def list_notifications() -> List[Dict[str, Any]]:
    try:
        db = get_db()
        return await db["notifications"].find({}).sort("createdAt", -1).to_list(None)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc


@router.post("/notifications", status_code=201)
async def create_notification(payload: NotificationPayload) -> Dict[str, Any]:
    try:
        db = get_db()
        now_iso = datetime.now(timezone.utc).isoformat()

        # Nếu có student_ids → ghi đúng schema để student app đọc được
        if payload.student_ids:
            docs = [
                {
                    "student_id": sid,
                    "type": payload.type,
                    "read": False,
                    "sender_role": payload.senderRole,
                    "payload": {
                        "title": payload.title,
                        "body": payload.content,
                    },
                    "created_at": now_iso,
                }
                for sid in payload.student_ids
            ]
            result = await db["notifications"].insert_many(docs)
            return {"ok": True, "count": len(result.inserted_ids)}

        # Không có student_ids → ghi schema cũ (teacher broadcast chung)
        new_notification = {
            "senderRole": payload.senderRole,
            "receiverRole": payload.receiverRole,
            "type": payload.type,
            "title": payload.title,
            "content": payload.content,
            "createdAt": now_iso,
        }
        result = await db["notifications"].insert_one(new_notification)
        new_notification["_id"] = str(result.inserted_id)
        return new_notification
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


@router.get("/schedules")
async def list_schedules() -> List[Dict[str, Any]]:
    try:
        db = get_db()
        return await db["schedules"].find({}).to_list(None)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc


@router.post("/schedules", status_code=201)
async def create_schedule(payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        db = get_db()
        result = await db["schedules"].insert_one(payload)
        payload["_id"] = result.inserted_id
        return payload
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc


@router.put("/schedules/{schedule_id}")
async def update_schedule(schedule_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        db = get_db()
        payload.pop("_id", None)
        result = await db["schedules"].update_one({"_id": ObjectId(schedule_id)}, {"$set": payload})
        return {"updated": result.modified_count}
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid schedule id") from exc


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str) -> Dict[str, Any]:
    try:
        db = get_db()
        result = await db["schedules"].delete_one({"_id": ObjectId(schedule_id)})
        return {"deleted": result.deleted_count}
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid schedule id") from exc


@router.get("/classes")
async def list_classes() -> List[str]:
    try:
        db = get_db()
        courses = await db["processed_courses"].find({}, {"module": 1, "presentation": 1, "_id": 0}).to_list(None)
        return sorted({f"{course.get('module')}-{course.get('presentation')}" for course in courses})
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc


@router.get("/rooms")
async def list_rooms() -> List[str]:
    return [
        "G2-101",
        "G2-102",
        "G2-103",
        "G2-201",
        "G2-202",
        "G2-203",
        "E3-101",
        "E3-102",
        "E3-201",
        "E3-202",
        "E3-301",
        "E3-302",
        "B1-101",
        "B1-102",
        "B1-201",
        "B1-202",
        "Online - Zoom",
        "Online - Teams",
    ]


@router.post("/ai/chat")
async def ai_chat(payload: ChatRequest) -> Dict[str, str]:
    reply = f"Tôi đã nhận câu hỏi: {payload.message}. Bạn có thể mở rộng logic này bằng model LLM trong bước tiếp theo."
    return {"reply": reply}
