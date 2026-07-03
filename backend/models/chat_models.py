from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum


class RoleType(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    SYSTEM = "system"  # Admin/ hệ thống


# ── Chat Message Model ───────────────────────────────────────
class ChatMessage(BaseModel):
    id: Optional[int] = None
    class_id: int
    sender_id: int          # student_id hoặc teacher_id
    role: RoleType
    content: str            # text message
    file_url: Optional[str] = None      # image/file url
    type: MessageType = MessageType.TEXT
    is_read: bool = False
    
    class Config:
        from_attributes = True


class ChatMessageCreate(BaseModel):
    class_id: int
    content: str
    file_url: Optional[str] = None
    role: RoleType = RoleType.STUDENT  # auto-detect được nhưng để rõ


class ChatMessageUpdate(BaseModel):
    is_read: Optional[bool] = None


class ChatMessageResponse(ChatMessage):
    sender_name: str
    timestamp: datetime
    
    class Config:
        from_attributes = True


# ── Notification Model ────────────────────────────────────────
class NotificationBase(BaseModel):
    student_id: int
    title: Optional[str] = None
    message: str
    type: Literal["chat", "alert", "reminder"] = "chat"
    chat_id: Optional[int] = None  # source từ chat nào
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NotificationCreate(BaseModel):
    student_id: int
    title: Optional[str] = None
    message: str
    type: Literal["chat", "alert", "reminder"] = "chat"
    chat_id: Optional[int] = None


class NotificationResponse(NotificationBase):
    id: Optional[int] = None
    
    class Config:
        from_attributes = True