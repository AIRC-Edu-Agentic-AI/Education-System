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
]
