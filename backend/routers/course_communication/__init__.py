"""Course communication routers."""

from fastapi import APIRouter

from .courses import router as courses_router


router = APIRouter(tags=["course_communication"])

# Include sub-routers
router.include_router(courses_router, prefix="/courses")

__all__ = ["router"]
