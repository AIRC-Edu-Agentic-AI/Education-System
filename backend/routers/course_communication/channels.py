"""Channel endpoints."""

from fastapi import APIRouter, HTTPException

from db.mongodb import get_db
from db.course_communication import (
    get_channel,
    get_course_channels,
)

router = APIRouter()


@router.get("/courses/{course_code}/channels")
async def list_course_channels(course_code: str):
    """List all channels for a course."""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database required")
    return await get_course_channels(db, course_code)


@router.get("/{channel_id}")
async def get_channel_info(channel_id: str):
    """Get channel information."""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database required")
    channel = await get_channel(db, channel_id)
    if channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel
