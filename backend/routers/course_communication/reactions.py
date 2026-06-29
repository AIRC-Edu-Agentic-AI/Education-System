"""Reaction endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.mongodb import get_db
from db.course_communication import react_to_message

router = APIRouter()


class ReactionRequest(BaseModel):
    user_id: int
    emoji: str


@router.post("/messages/{message_id}/reactions")
async def add_reaction(message_id: str, body: ReactionRequest):
    """Add a reaction to a message."""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database required")
    try:
        await react_to_message(db, message_id, body.user_id, body.emoji)
        return {"ok": True}
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
