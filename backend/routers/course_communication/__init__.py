"""Course communication routers."""

from fastapi import APIRouter

from .courses import router as courses_router
from .channels import router as channels_router


router = APIRouter(tags=["course_communication"])

# Include sub-routers
router.include_router(courses_router, prefix="/courses")
router.include_router(channels_router, prefix="/channels")


__all__ = ["router"]
