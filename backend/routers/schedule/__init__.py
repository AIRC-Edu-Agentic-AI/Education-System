"""Schedule routers package.

Exports:
    student_router  — Student schedule/timetable/study-plan endpoints
    teacher_router  — Teacher schedule management endpoints
"""
from .student import router as student_router
from .teacher import router as teacher_router

__all__ = ["student_router", "teacher_router"]