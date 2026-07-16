"""Constants for course communication module."""

COURSE_STATUS_ACTIVE = "active"
COURSE_STATUS_ARCHIVED = "archived"
COURSE_STATUS_DELETED = "deleted"

CHANNEL_TYPE_ANNOUNCEMENT = "announcement"
CHANNEL_TYPE_DISCUSSION = "discussion"

DEFAULT_COURSE_SETTINGS = {
    "notification_window": {"start": "08:00", "end": "18:00"},
    "mentions_only": False,
    "mute_discussion": False,
}

ANNOUNCEMENT_CHANNEL = {
    "type": CHANNEL_TYPE_ANNOUNCEMENT,
    "name": "Thông báo lớp",
    "is_read_only": True,
    "allowed_post_roles": ["instructor", "class_rep"],
}

DISCUSSION_CHANNEL = {
    "type": CHANNEL_TYPE_DISCUSSION,
    "name": "Thảo luận",
    "is_read_only": False,
    "allowed_post_roles": ["student", "instructor", "class_rep"],
}
