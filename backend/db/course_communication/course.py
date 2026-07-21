"""Course management functions."""

from .constants import COURSE_STATUS_ACTIVE, COURSE_STATUS_ARCHIVED, COURSE_STATUS_DELETED
from .utils import now_iso, to_json
from .audit import record_audit
from .channel import _ensure_course_channels


async def ensure_course(db, course_code: str, title: str, presentation: str = "", term: str = "2024A", instructor_ids: list[int] | None = None, class_rep_ids: list[int] | None = None):
    """Ensure course exists, create if not, update if exists."""
    instructor_ids = instructor_ids or []
    class_rep_ids = class_rep_ids or []
    now = now_iso()
    course = await db.courses.find_one({"course_code": course_code})
    if course is None:
        course = {
            "course_code": course_code,
            "title": title,
            "presentation": presentation,
            "term": term,
            "instructors": instructor_ids,
            "class_reps": class_rep_ids,
            "members": [],
            "status": COURSE_STATUS_ACTIVE,
            "settings": {},
            "created_at": now,
            "updated_at": now,
            "archived_at": None,
            "retention_expires_at": None,
        }
        from .course_settings import DEFAULT_SETTINGS
        course["settings"] = dict(DEFAULT_SETTINGS)
        await db.courses.insert_one(course)
    else:
        update_data = {}
        if course.get("title") != title:
            update_data["title"] = title
        if presentation and course.get("presentation") != presentation:
            update_data["presentation"] = presentation
        if instructor_ids:
            update_data["instructors"] = list(set(course.get("instructors", []) + instructor_ids))
        if class_rep_ids:
            update_data["class_reps"] = list(set(course.get("class_reps", []) + class_rep_ids))
        if update_data:
            update_data["updated_at"] = now
            await db.courses.update_one(
                {"course_code": course_code},
                {"$set": update_data},
            )
        course = await db.courses.find_one({"course_code": course_code})

    await _ensure_course_channels(db, course_code)
    return course


async def get_course(db, course_code: str):
    """Get course by code."""
    course = await db.courses.find_one({"course_code": course_code})
    return to_json(course)


async def get_student_courses(db, student_id: int):
    """Get all courses for a student."""
    courses = await db.courses.find({"members": student_id, "status": {"$ne": COURSE_STATUS_DELETED}}).to_list(length=50)
    return [to_json(c) for c in courses]


async def enroll_student_in_course(db, student_id: int, course_code: str, title: str, presentation: str = "", term: str = "2024A", instructor_ids: list[int] | None = None, class_rep_ids: list[int] | None = None):
    """Enroll a student in a course."""
    course = await ensure_course(db, course_code, title, presentation, term, instructor_ids, class_rep_ids)

    await db.students.update_one(
        {"student_id": student_id},
        {"$addToSet": {"enrollments": {
            "code_module": course_code,
            "code_presentation": presentation,
            "title": title,
            "module_length": 0,
            "registration_date": now_iso(),
            "unregistration_date": None,
            "final_result": None,
            "assessments": [],
            "vle_summary": {},
        }}},
    )

    await db.courses.update_one(
        {"course_code": course_code},
        {"$addToSet": {"members": student_id, "instructors": {"$each": instructor_ids or []}, "class_reps": {"$each": class_rep_ids or []}}},
    )

    await record_audit(db, "enroll", course_code, student_id, {"action": "student_enrolled"})
    return to_json(await db.courses.find_one({"course_code": course_code}))


async def withdraw_student_from_course(db, student_id: int, course_code: str):
    """Withdraw a student from a course."""
    student_update = await db.students.update_one(
        {"student_id": student_id},
        {"$pull": {"enrollments": {"code_module": course_code}}},
    )
    if student_update.modified_count == 0:
        return False
    await db.courses.update_one(
        {"course_code": course_code},
        {"$pull": {"members": student_id}},
    )
    await record_audit(db, "withdraw", course_code, student_id, {"action": "student_withdrawn"})
    return True
