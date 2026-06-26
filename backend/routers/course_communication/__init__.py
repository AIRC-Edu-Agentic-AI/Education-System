"""Course communication routers."""

from fastapi import APIRouter

from .courses import router as courses_router
from .channels import router as channels_router
from .messages import router as messages_router
from .reactions import router as reactions_router
from .course_settings import router as course_settings_router

router = APIRouter(prefix="/course-communication", tags=["course-communication"])

# Include sub-routers
router.include_router(courses_router)
router.include_router(channels_router)
router.include_router(messages_router)
router.include_router(reactions_router)
router.include_router(course_settings_router)

__all__ = ["router"]
