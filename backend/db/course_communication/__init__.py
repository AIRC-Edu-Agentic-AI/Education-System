"""Course communication module."""

# Course functions
from .course import (
    ensure_course,
    get_course,
    get_student_courses,
    enroll_student_in_course,
    withdraw_student_from_course,
)

# Channel functions
from .channel import (
    get_course_channels,
    get_channel,
)

# Message functions
from .message import (
    get_channel_messages,
    add_channel_message,
)

# Reaction functions
from .reactions import (
    react_to_message,
)

# Settings functions
from .course_settings import (
    archive_course,
    update_course_settings,
)

# Constants
from .constants import (
    COURSE_STATUS_ACTIVE,
    COURSE_STATUS_ARCHIVED,
    COURSE_STATUS_DELETED,
    CHANNEL_TYPE_ANNOUNCEMENT,
    CHANNEL_TYPE_DISCUSSION,
)

__all__ = [
    # Course
    "ensure_course",
    "get_course",
    "get_student_courses",
    "enroll_student_in_course",
    "withdraw_student_from_course",
    # Channel
    "get_course_channels",
    "get_channel",
    # Message
    "get_channel_messages",
    "add_channel_message",
    # Reaction
    "react_to_message",
    # Settings
    "archive_course",
    "update_course_settings",
    # Constants
    "COURSE_STATUS_ACTIVE",
    "COURSE_STATUS_ARCHIVED",
    "COURSE_STATUS_DELETED",
    "CHANNEL_TYPE_ANNOUNCEMENT",
    "CHANNEL_TYPE_DISCUSSION",
]
