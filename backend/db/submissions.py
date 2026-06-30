"""Assignment submission storage and student record updates."""

from datetime import datetime, timezone

from db.mock_data import MOCK_STUDENT, MOCK_SCHEDULE

# In-memory store when MongoDB is unavailable (demo / mock mode).
_MOCK_SUBMISSIONS: dict[tuple[int, int], dict] = {}


def _current_module_day(schedule_doc: dict | None = None) -> int:
    week = (schedule_doc or MOCK_SCHEDULE).get("current_week", 7)
    return week * 7 - 3


def _find_assessment(doc: dict, id_assessment: int) -> tuple[dict | None, dict | None]:
    for enrollment in doc.get("enrollments", []):
        for assessment in enrollment.get("assessments", []):
            if assessment.get("id_assessment") == id_assessment:
                return enrollment, assessment
    return None, None


async def get_submission(db, student_id: int, id_assessment: int) -> dict | None:
    if db is not None:
        doc = await db.submissions.find_one(
            {"student_id": student_id, "id_assessment": id_assessment}
        )
        if not doc:
            return None
        doc["_id"] = str(doc["_id"])
        return doc

    stored = _MOCK_SUBMISSIONS.get((student_id, id_assessment))
    if stored:
        return dict(stored)
    return None


async def submit_assignment(
    db,
    student_id: int,
    id_assessment: int,
    content: str,
) -> dict:
    content = content.strip()
    if not content:
        raise ValueError("Nội dung bài nộp không được để trống.")

    if db is not None:
        student_doc = await db.students.find_one({"student_id": student_id})
        if not student_doc:
            raise LookupError(f"Student {student_id} not found")

        enrollment, assessment = _find_assessment(student_doc, id_assessment)
        if not assessment:
            raise LookupError(f"Assessment {id_assessment} not found")
        if assessment.get("submitted_date"):
            raise ValueError("Bài tập đã được nộp trước đó.")

        schedule_doc = await db.timetable_blocks.find_one({"student_id": student_id})
        submitted_day = _current_module_day(schedule_doc)
        now = datetime.now(timezone.utc).isoformat()

        submission = {
            "student_id": student_id,
            "id_assessment": id_assessment,
            "course_code": enrollment.get("code_module", ""),
            "content": content,
            "submitted_at": now,
            "submitted_day": submitted_day,
            "status": "submitted",
        }
        await db.submissions.update_one(
            {"student_id": student_id, "id_assessment": id_assessment},
            {"$set": submission},
            upsert=True,
        )
        await db.students.update_one(
            {"student_id": student_id},
            {"$set": {"enrollments.$[e].assessments.$[a].submitted_date": submitted_day}},
            array_filters=[
                {"e.code_module": enrollment.get("code_module")},
                {"a.id_assessment": id_assessment},
            ],
        )
        submission["_id"] = f"{student_id}_{id_assessment}"
        return submission

    # Mock mode
    student_doc = MOCK_STUDENT
    enrollment, assessment = _find_assessment(student_doc, id_assessment)
    if not assessment:
        raise LookupError(f"Assessment {id_assessment} not found")
    if assessment.get("submitted_date"):
        raise ValueError("Bài tập đã được nộp trước đó.")

    submitted_day = _current_module_day()
    now = datetime.now(timezone.utc).isoformat()
    assessment["submitted_date"] = submitted_day

    submission = {
        "_id": f"mock_{student_id}_{id_assessment}",
        "student_id": student_id,
        "id_assessment": id_assessment,
        "course_code": enrollment.get("code_module", "") if enrollment else "",
        "content": content,
        "submitted_at": now,
        "submitted_day": submitted_day,
        "status": "submitted",
    }
    _MOCK_SUBMISSIONS[(student_id, id_assessment)] = submission
    return submission
