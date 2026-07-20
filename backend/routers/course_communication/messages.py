"""Message endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.mongodb import get_db
from db.course_communication import (
    add_channel_message,
    get_channel_messages,
)

router = APIRouter()


class MessageRequest(BaseModel):
    sender_id: int
    content: str
    parent_id: str | None = None


@router.get("/{channel_id}/messages")
async def list_channel_messages(channel_id: str, parent_id: str | None = None):
    """List all messages in a channel."""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database required")
    return await get_channel_messages(db, channel_id, parent_id)


@router.post("/{channel_id}/messages")
async def post_channel_message(channel_id: str, body: MessageRequest):
    """Post a message to a channel."""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database required")
    try:
        msg = await add_channel_message(db, channel_id, body.sender_id, body.content, body.parent_id)
        
        try:
            from routers.realtime_chat import manager
            from db.course_communication.channel import get_channel
            channel = await get_channel(db, channel_id)
            if channel:
                broadcast_data = {"type": "new_message", "message": msg}
                await manager.broadcast_to_channel(channel, broadcast_data)
        except Exception as e:
            print(f"Error broadcasting: {e}")
            
        return msg
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
