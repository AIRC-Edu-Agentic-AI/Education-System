"""Course settings and management endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.mongodb import get_db
from db.course_communication import (
    archive_course,
    update_course_settings,
)

router = APIRouter()


class CourseSettingsRequest(BaseModel):
    notification_window: dict | None = None
    mentions_only: bool | None = None
    mute_discussion: bool | None = None


@router.patch("/{course_code}/archive")
async def archive_course_space(course_code: str, retention_days: int | None = 180):
    """Archive a course with retention policy."""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database required")
    await archive_course(db, course_code, retention_days or 180)
    return {"ok": True}


@router.patch("/{course_code}/settings")
async def patch_course_settings(course_code: str, body: CourseSettingsRequest):
    """Update course settings."""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database required")
    settings = {}
    if body.notification_window is not None:
        settings["notification_window"] = body.notification_window
    if body.mentions_only is not None:
        settings["mentions_only"] = body.mentions_only
    if body.mute_discussion is not None:
        settings["mute_discussion"] = body.mute_discussion
    course = await update_course_settings(db, course_code, settings)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found or invalid settings")
    return course
