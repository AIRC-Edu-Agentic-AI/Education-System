from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class GroupMessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"
    DOCUMENT = "document"  #  THÊM


class GroupResourceType(str, Enum):
    DOCUMENT = "document"
    LINK = "link"
    IMAGE = "image"
    VIDEO = "video"


# ── Group Message ────────────────────────────────────────────────
class GroupMessage(BaseModel):
    id: Optional[str] = None
    group_id: str
    sender_id: str
    sender_name: str
    content: str
    file_url: Optional[str] = None
    file_name: Optional[str] = None      # ⭐ THÊM
    file_size: Optional[int] = None      # ⭐ THÊM
    file_type: Optional[str] = None      # ⭐ THÊM
    type: GroupMessageType = GroupMessageType.TEXT
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_read: bool = False

    class Config:
        populate_by_name = True


class GroupMessageCreate(BaseModel):
    content: str
    file_url: Optional[str] = None
    file_name: Optional[str] = None     
    file_size: Optional[int] = None     
    file_type: Optional[str] = None      
    type: str = "text" 


class GroupMessageResponse(GroupMessage):
    id: str
    timestamp: datetime
    file_name: Optional[str] = None    
    file_size: Optional[int] = None   
    file_type: Optional[str] = None   


# ── Group Resource ────────────────────────────────────────────────
class GroupResource(BaseModel):
    id: Optional[str] = None
    group_id: str
    title: str
    type: GroupResourceType = GroupResourceType.DOCUMENT
    url: str
    uploaded_by: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True


class GroupResourceCreate(BaseModel):
    title: str
    type: GroupResourceType = GroupResourceType.DOCUMENT
    url: str


class GroupResourceResponse(GroupResource):
    id: str
    uploaded_by_name: Optional[str] = None


# ── Study Group ────────────────────────────────────────────────────
class StudyGroup(BaseModel):
    id: Optional[str] = None
    group_code: str
    name: str
    description: str = ""
    created_by: str
    members: List[str] = []
    messages: List[GroupMessage] = []
    resources: List[GroupResource] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active_at: Optional[datetime] = None
    member_count: Optional[int] = None

    class Config:
        populate_by_name = True


class StudyGroupCreate(BaseModel):
    name: str
    description: Optional[str] = ""


class StudyGroupJoin(BaseModel):
    group_code: str


class StudyGroupResponse(StudyGroup):
    id: str
    created_at: datetime
    member_count: Optional[int] = None