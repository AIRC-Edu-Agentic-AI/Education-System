"""Course settings and management functions."""

import datetime
from datetime import timezone

from .constants import COURSE_STATUS_ARCHIVED
from .utils import now_iso, to_json
from .audit import record_audit

DEFAULT_SETTINGS = {
    "notification_window": {"start": "08:00", "end": "18:00"},
    "mentions_only": False,
    "mute_discussion": False,
}


async def archive_course(db, course_code: str, retention_days: int = 180):
    """Archive a course with retention policy."""
    now = now_iso()
    expire_at = (datetime.datetime.now(timezone.utc) + datetime.timedelta(days=retention_days)).isoformat()
    await db.courses.update_one(
        {"course_code": course_code},
        {"$set": {
            "status": COURSE_STATUS_ARCHIVED,
            "archived_at": now,
            "retention_expires_at": expire_at,
            "updated_at": now,
        }},
    )
    await db.channels.update_many(
        {"course_code": course_code},
        {"$set": {"status": COURSE_STATUS_ARCHIVED, "updated_at": now}},
    )
    await record_audit(db, "course_archived", course_code, None, {"retention_expires_at": expire_at})
    return True


async def update_course_settings(db, course_code: str, settings: dict):
    """Update course settings."""
    valid_keys = {"notification_window", "mentions_only", "mute_discussion"}
    filtered = {k: v for k, v in settings.items() if k in valid_keys}
    if not filtered:
        return None
    now = now_iso()
    await db.courses.update_one(
        {"course_code": course_code},
        {"$set": {"settings": filtered, "updated_at": now}},
    )
    await record_audit(db, "settings_updated", course_code, None, filtered)
    course = await db.courses.find_one({"course_code": course_code})
    return to_json(course)
