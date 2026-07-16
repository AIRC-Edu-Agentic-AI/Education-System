from uuid import uuid4
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from datetime import datetime
import secrets
from fastapi import File, UploadFile, Form
import shutil
import os

from db.mongodb import get_db
from db.study_group_repository import StudyGroupRepository
from models.study_group_models import (
    StudyGroupCreate, StudyGroupJoin, StudyGroupResponse,
    GroupMessageCreate, GroupMessageResponse,
    GroupResourceCreate, GroupResourceResponse,
    GroupMessageType
)

router = APIRouter(prefix="/study-groups", tags=["Study Groups"])

# ── MOCK DATA ──────────────────────────────────────────────────────
MOCK_GROUPS = [
    {
        "id": "mock_001",
        "group_code": "GRP-ABC123",
        "name": "Nhóm học DATA201",
        "description": "Nhóm học tập môn Phân tích Dữ liệu & Thống kê",
        "created_by": "28400",
        "members": ["28400", "28401", "28402"],
        "messages": [],
        "resources": [],
        "created_at": datetime.utcnow().isoformat(),
        "last_active_at": datetime.utcnow().isoformat(),
        "member_count": 3
    },
    {
        "id": "mock_002",
        "group_code": "GRP-DEF456",
        "name": "Nhóm ôn thi COMP101",
        "description": "Ôn tập Lập trình Python",
        "created_by": "28400",
        "members": ["28400", "28405"],
        "messages": [],
        "resources": [],
        "created_at": datetime.utcnow().isoformat(),
        "last_active_at": datetime.utcnow().isoformat(),
        "member_count": 2
    },
    {
        "id": "mock_003",
        "group_code": "GRP-GHI789",
        "name": "Nhóm STAT110",
        "description": "Xác suất & Thống kê Suy luận",
        "created_by": "28410",
        "members": ["28410", "28411", "28412"],
        "messages": [],
        "resources": [],
        "created_at": datetime.utcnow().isoformat(),
        "last_active_at": datetime.utcnow().isoformat(),
        "member_count": 3
    }
]


def generate_mock_group_code() -> str:
    return f"GRP-{secrets.token_hex(3).upper()}"


def mock_to_response(mock_dict: dict) -> dict:
    return {
        "id": str(mock_dict["id"]),
        "group_code": str(mock_dict["group_code"]),
        "name": str(mock_dict["name"]),
        "description": str(mock_dict["description"] or ""),
        "created_by": str(mock_dict["created_by"]),
        "members": [str(m) for m in mock_dict.get("members", [])],  # ⭐ Đảm bảo là List[str]
        "messages": mock_dict.get("messages", []),
        "resources": mock_dict.get("resources", []),
        "created_at": str(mock_dict["created_at"]),
        "last_active_at": str(mock_dict.get("last_active_at")) if mock_dict.get("last_active_at") else None,
        "member_count": int(mock_dict.get("member_count", len(mock_dict.get("members", []))))  # ⭐ Đảm bảo là int
    }

# ── Group CRUD ────────────────────────────────────────────────────

@router.post("/create", response_model=StudyGroupResponse)
async def create_group(
    data: StudyGroupCreate,
    student_id: str,
    db=Depends(get_db)
):
    try:
        print(f"📝 Creating group for student: {student_id}")
        print(f"📝 Data: {data}")
        
        if db:
            repo = StudyGroupRepository(db)
            student = await db.students.find_one({"student_id": student_id})
            if not student:
                raise HTTPException(status_code=404, detail="Student not found")
            group = await repo.create_group(student_id, data)
            print(f"✅ Group created in DB: {group.id}")
            return group
        
        # Mock mode
        new_group = {
            "id": f"mock_{len(MOCK_GROUPS) + 1:03d}",
            "group_code": generate_mock_group_code(),
            "name": data.name,
            "description": data.description or "",
            "created_by": student_id,
            "members": [student_id],
            "messages": [],
            "resources": [],
            "created_at": datetime.utcnow().isoformat(),
            "last_active_at": datetime.utcnow().isoformat(),
            "member_count": 1
        }
        MOCK_GROUPS.append(new_group)
        
        # ⭐ LOG DỮ LIỆU TRẢ VỀ
        result = mock_to_response(new_group)
        print(f"✅ Group created in MOCK: {result}")
        return result
        
    except Exception as e:
        print(f"❌ Error creating group: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    if db:
        repo = StudyGroupRepository(db)
        student = await db.students.find_one({"student_id": student_id})
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        group = await repo.create_group(student_id, data)
        return group
    
    new_group = {
        "id": f"mock_{len(MOCK_GROUPS) + 1:03d}",
        "group_code": generate_mock_group_code(),
        "name": data.name,
        "description": data.description or "",
        "created_by": student_id,
        "members": [student_id],
        "messages": [],
        "resources": [],
        "created_at": datetime.utcnow().isoformat(),
        "last_active_at": datetime.utcnow().isoformat(),
        "member_count": 1
    }
    MOCK_GROUPS.append(new_group)
    return mock_to_response(new_group)


@router.post("/join", response_model=StudyGroupResponse)
async def join_group(
    data: StudyGroupJoin,
    student_id: str,
    db=Depends(get_db)
):
    if db:
        repo = StudyGroupRepository(db)
        student = await db.students.find_one({"student_id": student_id})
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        group = await repo.join_group(student_id, data.group_code)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found or invalid code")
        return group
    
    group_code = data.group_code.upper()
    for group in MOCK_GROUPS:
        if group["group_code"] == group_code:
            if student_id not in group["members"]:
                group["members"].append(student_id)
                group["member_count"] = len(group["members"])
            return mock_to_response(group)
    
    raise HTTPException(status_code=404, detail="Group not found or invalid code")


@router.get("/my-groups", response_model=List[StudyGroupResponse])
async def get_my_groups(
    student_id: str,
    db=Depends(get_db)
):
    if db:
        repo = StudyGroupRepository(db)
        groups = await repo.get_my_groups(student_id)
        return groups
    
    user_groups = [
        mock_to_response(group) for group in MOCK_GROUPS
        if student_id in group["members"]
    ]
    return user_groups


@router.get("/{group_id}", response_model=StudyGroupResponse)
async def get_group_detail(
    group_id: str,
    student_id: str,
    db=Depends(get_db)
):
    if db:
        repo = StudyGroupRepository(db)
        group = await repo.get_group(group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        if student_id not in group.members:
            raise HTTPException(status_code=403, detail="Not a member of this group")
        group.member_count = len(group.members)
        return group
    
    for group in MOCK_GROUPS:
        if group["id"] == group_id:
            if student_id not in group["members"]:
                raise HTTPException(status_code=403, detail="Not a member of this group")
            return mock_to_response(group)
    
    raise HTTPException(status_code=404, detail="Group not found")


@router.delete("/{group_id}/leave")
async def leave_group(
    group_id: str,
    student_id: str,
    db=Depends(get_db)
):
    if db:
        repo = StudyGroupRepository(db)
        group = await repo.get_group(group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        if student_id not in group.members:
            raise HTTPException(status_code=403, detail="Not a member")
        if group.created_by == student_id and len(group.members) > 1:
            raise HTTPException(
                status_code=400,
                detail="Creator cannot leave group with other members."
            )
        await repo.leave_group(group_id, student_id)
        return {"message": "Left group successfully"}
    
    for group in MOCK_GROUPS:
        if group["id"] == group_id:
            if student_id not in group["members"]:
                raise HTTPException(status_code=403, detail="Not a member")
            if group["created_by"] == student_id and len(group["members"]) > 1:
                raise HTTPException(
                    status_code=400,
                    detail="Creator cannot leave group with other members."
                )
            group["members"].remove(student_id)
            group["member_count"] = len(group["members"])
            return {"message": "Left group successfully"}
    
    raise HTTPException(status_code=404, detail="Group not found")


@router.post("/{group_id}/messages", response_model=GroupMessageResponse)
async def send_group_message(
    group_id: str,
    data: GroupMessageCreate,
    student_id: str,
    db=Depends(get_db)
):
    """Gửi tin nhắn trong nhóm"""
    
    # ⭐ THÊM DEBUG
    print("="*50)
    print("📨 Received message data:")
    print(f"  group_id: {group_id}")
    print(f"  student_id: {student_id}")
    print(f"  content: {data.content}")
    print(f"  file_url: {data.file_url}")
    print(f"  file_name: {data.file_name}")
    print(f"  file_size: {data.file_size}")
    print(f"  file_type: {data.file_type}")
    print(f"  type: {data.type}")
    print("="*50)
    
    # ⭐ Nếu có database, dùng database
    if db:
        repo = StudyGroupRepository(db)
        group = await repo.get_group(group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        if student_id not in group.members:
            raise HTTPException(status_code=403, detail="Not a member")
        
        student = await db.students.find_one({"student_id": student_id})
        sender_name = student.get("short_name", student.get("full_name", "Unknown"))
        
        message = await repo.add_message_with_sender(
            group_id=group_id,
            student_id=student_id,
            sender_name=sender_name,
            content=data.content,
            file_url=data.file_url,
            file_name=data.file_name,
            file_size=data.file_size,
            file_type=data.file_type,
            msg_type=data.type
        )
        if not message:
            raise HTTPException(status_code=400, detail="Failed to send message")
        return message
    
    # ⭐ Nếu KHÔNG có database (mock mode), dùng mock data
    for group in MOCK_GROUPS:
        if group["id"] == group_id:
            if student_id not in group["members"]:
                raise HTTPException(status_code=403, detail="Not a member")
            
            # Tạo tin nhắn mới
            msg_type = data.type if isinstance(data.type, str) else "text"
            
            message = {
                "id": f"msg_{len(group.get('messages', [])) + 1:03d}",
                "group_id": group_id,
                "sender_id": student_id,
                "sender_name": f"User_{student_id}",
                "content": data.content,
                "file_url": data.file_url,
                "file_name": data.file_name,
                "file_size": data.file_size,
                "file_type": data.file_type,
                "type": msg_type,
                "timestamp": datetime.utcnow().isoformat(),
                "is_read": False
            }
            group.setdefault("messages", []).append(message)
            return message
    
    raise HTTPException(status_code=404, detail="Group not found")


@router.get("/{group_id}/messages", response_model=List[GroupMessageResponse])
async def get_group_messages(
    group_id: str,
    student_id: str,
    limit: int = 50,
    offset: int = 0,
    db=Depends(get_db)
):
    if db:
        repo = StudyGroupRepository(db)
        group = await repo.get_group(group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        if student_id not in group.members:
            raise HTTPException(status_code=403, detail="Not a member")
        messages = await repo.get_messages(group_id, limit, offset)
        return messages
    
    for group in MOCK_GROUPS:
        if group["id"] == group_id:
            if student_id not in group["members"]:
                raise HTTPException(status_code=403, detail="Not a member")
            messages = group.get("messages", [])
            start = offset
            end = offset + limit
            return messages[start:end] if start < len(messages) else []
    
    raise HTTPException(status_code=404, detail="Group not found")


# ── Resources ─────────────────────────────────────────────────────

@router.post("/{group_id}/resources", response_model=GroupResourceResponse)
async def add_group_resource(
    group_id: str,
    data: GroupResourceCreate,
    student_id: str,
    db=Depends(get_db)
):
    if db:
        repo = StudyGroupRepository(db)
        group = await repo.get_group(group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        if student_id not in group.members:
            raise HTTPException(status_code=403, detail="Not a member")
        resource = await repo.add_resource(group_id, data, student_id)
        if not resource:
            raise HTTPException(status_code=400, detail="Failed to add resource")
        return resource
    
    for group in MOCK_GROUPS:
        if group["id"] == group_id:
            if student_id not in group["members"]:
                raise HTTPException(status_code=403, detail="Not a member")
            
            resource = {
                "id": f"res_{len(group.get('resources', [])) + 1:03d}",
                "group_id": group_id,
                "title": data.title,
                "type": data.type or "document",
                "url": data.url,
                "uploaded_by": student_id,
                "uploaded_at": datetime.utcnow().isoformat()
            }
            group.setdefault("resources", []).append(resource)
            return resource
    
    raise HTTPException(status_code=404, detail="Group not found")


@router.get("/{group_id}/resources", response_model=List[GroupResourceResponse])
async def get_group_resources(
    group_id: str,
    student_id: str,
    db=Depends(get_db)
):
    if db:
        repo = StudyGroupRepository(db)
        group = await repo.get_group(group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        if student_id not in group.members:
            raise HTTPException(status_code=403, detail="Not a member")
        resources = await repo.get_resources(group_id)
        return resources
    
    for group in MOCK_GROUPS:
        if group["id"] == group_id:
            if student_id not in group["members"]:
                raise HTTPException(status_code=403, detail="Not a member")
            return group.get("resources", [])
    
    raise HTTPException(status_code=404, detail="Group not found")


# ── Upload File ──────────────────────────────────────────────────

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/{group_id}/upload")
async def upload_file(
    group_id: str,
    student_id: str = Form(...),
    file: UploadFile = File(...)
):
    """Upload file vào nhóm"""
    file_extension = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid4().hex}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {
        "url": f"/uploads/{unique_name}",
        "name": file.filename,
        "size": os.path.getsize(file_path)
    }