from typing import Optional, List
from datetime import datetime
import secrets
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

# ✅ SỬA: Bỏ prefix "backend."
from models.study_group_models import (
    StudyGroup, StudyGroupCreate, 
    GroupMessage, GroupMessageCreate,
    GroupResource, GroupResourceCreate
)


def generate_group_code() -> str:
    """Tạo mã nhóm ngẫu nhiên 6 ký tự"""
    return f"GRP-{secrets.token_hex(3).upper()}"


class StudyGroupRepository:
    def __init__(self, db: AsyncIOMotorDatabase): # type: ignore
        self.db = db
        self.collection = db.study_groups

    async def create_group(
        self, 
        student_id: str,
        data: StudyGroupCreate
    ) -> StudyGroup:
        """Tạo nhóm mới"""
        group_code = generate_group_code()
        while await self.collection.find_one({"group_code": group_code}):
            group_code = generate_group_code()

        group_dict = {
            "group_code": group_code,
            "name": data.name,
            "description": data.description or "",
            "created_by": student_id,
            "members": [student_id],
            "messages": [],
            "resources": [],
            "created_at": datetime.utcnow(),
            "last_active_at": datetime.utcnow()
        }

        result = await self.collection.insert_one(group_dict)
        group_dict["id"] = str(result.inserted_id)
        return StudyGroup(**group_dict)

    async def join_group(self, student_id: str, group_code: str) -> Optional[StudyGroup]:
        """Tham gia nhóm bằng mã"""
        group = await self.collection.find_one({"group_code": group_code})
        if not group:
            return None

        if student_id in group.get("members", []):
            return StudyGroup(**group)

        await self.collection.update_one(
            {"_id": group["_id"]},
            {
                "$push": {"members": student_id},
                "$set": {"last_active_at": datetime.utcnow()}
            }
        )

        updated = await self.collection.find_one({"_id": group["_id"]})
        return StudyGroup(**updated) if updated else None

    async def get_my_groups(self, student_id: str) -> List[StudyGroup]:
        """Lấy danh sách nhóm của sinh viên"""
        cursor = self.collection.find({"members": student_id})
        groups = await cursor.to_list(length=100)
        return [StudyGroup(**g) for g in groups]

    async def get_group(self, group_id: str) -> Optional[StudyGroup]:
        """Lấy chi tiết nhóm"""
        if not ObjectId.is_valid(group_id):
            return None
        group = await self.collection.find_one({"_id": ObjectId(group_id)})
        return StudyGroup(**group) if group else None

    async def get_group_by_code(self, group_code: str) -> Optional[StudyGroup]:
        """Lấy nhóm theo mã"""
        group = await self.collection.find_one({"group_code": group_code})
        return StudyGroup(**group) if group else None

    async def leave_group(self, group_id: str, student_id: str) -> bool:
        """Rời nhóm"""
        if not ObjectId.is_valid(group_id):
            return False
        
        result = await self.collection.update_one(
            {"_id": ObjectId(group_id)},
            {"$pull": {"members": student_id}}
        )
        return result.modified_count > 0

    async def add_message_with_sender(
        self, 
        group_id: str, 
        student_id: str,
        sender_name: str,
        content: str,
        file_url: Optional[str] = None,
        file_name: Optional[str] = None,    # ⭐ THÊM
        file_size: Optional[int] = None,    # ⭐ THÊM
        file_type: Optional[str] = None,    # ⭐ THÊM
        msg_type: str = "text"
    ) -> Optional[GroupMessage]:
        """Thêm tin nhắn vào nhóm với sender_id"""
        if not ObjectId.is_valid(group_id):
            return None

        message = {
            "sender_id": student_id,
            "sender_name": sender_name,
            "content": content,
            "file_url": file_url,
            "file_name": file_name,
            "file_size": file_size,
            "file_type": file_type,
            "type": msg_type,
            "timestamp": datetime.utcnow().isoformat(),
            "is_read": False
        }

        result = await self.collection.update_one(
            {"_id": ObjectId(group_id)},
            {
                "$push": {"messages": message},
                "$set": {"last_active_at": datetime.utcnow()}
            }
        )

        if result.modified_count > 0:
            return GroupMessage(**message)
        return None

    async def get_messages(
        self, 
        group_id: str, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[GroupMessage]:
        """Lấy tin nhắn trong nhóm"""
        if not ObjectId.is_valid(group_id):
            return []

        group = await self.collection.find_one(
            {"_id": ObjectId(group_id)},
            {"messages": {"$slice": [-offset - limit, limit]}}
        )
        if not group:
            return []
        
        messages = group.get("messages", [])
        return [GroupMessage(**m) for m in messages]

    async def add_resource(
        self, 
        group_id: str, 
        data: GroupResourceCreate,
        uploaded_by: str
    ) -> Optional[GroupResource]:
        """Thêm tài nguyên vào nhóm"""
        if not ObjectId.is_valid(group_id):
            return None

        resource_dict = {
            "group_id": group_id,
            "title": data.title,
            "type": data.type,
            "url": data.url,
            "uploaded_by": uploaded_by,
            "uploaded_at": datetime.utcnow()
        }

        result = await self.collection.update_one(
            {"_id": ObjectId(group_id)},
            {"$push": {"resources": resource_dict}}
        )

        if result.modified_count > 0:
            return GroupResource(**resource_dict)
        return None

    async def get_resources(self, group_id: str) -> List[GroupResource]:
        """Lấy danh sách tài nguyên trong nhóm"""
        if not ObjectId.is_valid(group_id):
            return []

        group = await self.collection.find_one(
            {"_id": ObjectId(group_id)},
            {"resources": 1}
        )
        if not group:
            return []
        
        resources = group.get("resources", [])
        return [GroupResource(**r) for r in resources]