"""
Seed Sample Smart Study Groups in MongoDB Atlas
Creates initial sample study groups for demo student 28400 and peers.
"""

import asyncio
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

SAMPLE_STUDY_GROUPS = [
    {
        "group_code": "GRP-DATA201",
        "name": "Nhóm 1 - DATA201 (Cân bằng học lực)",
        "description": "Nhóm học tập Phân tích dữ liệu & Thống kê. Trưởng nhóm: Nguyễn Văn An",
        "created_by": "teacher",
        "leader_id": "28400",
        "members": ["28400", "28401", "28402", "28405"],
        "messages": [
            {
                "id": "msg_001",
                "sender_id": "system",
                "sender_name": "Hệ thống",
                "content": "🎉 Chào mừng các bạn đến với nhóm học tập DATA201! Trưởng nhóm: Nguyễn Văn An.",
                "type": "system",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "is_read": False,
            },
            {
                "id": "msg_002",
                "sender_id": "28400",
                "sender_name": "Nguyễn Văn An",
                "content": "Chào cả nhóm! Mình đã xem qua tài liệu tuần này của môn DATA201 rồi, tối nay 20h nhóm mình trao đổi nhé!",
                "type": "text",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "is_read": True,
            }
        ],
        "resources": [
            {
                "id": "res_001",
                "title": "Tài liệu ôn tập TMA 01 - Phân tích dữ liệu",
                "type": "document",
                "url": "https://example.com/docs/data201_tma01.pdf",
                "uploaded_by": "28400",
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
            }
        ],
        "course_module": "DATA201",
        "course_presentation": "2024A",
        "strategy": "balanced",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_active_at": datetime.now(timezone.utc).isoformat(),
        "member_count": 4,
    },
    {
        "group_code": "GRP-COMP101",
        "name": "Nhóm 2 - COMP101 (Đôi bạn cùng tiến)",
        "description": "Nhóm ôn tập lập trình Python và cấu trúc dữ liệu.",
        "created_by": "teacher",
        "leader_id": "28400",
        "members": ["28400", "28410", "28412"],
        "messages": [
            {
                "id": "msg_001",
                "sender_id": "system",
                "sender_name": "Hệ thống",
                "content": "🎉 Chào mừng các bạn đến với nhóm học tập COMP101!",
                "type": "system",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "is_read": False,
            }
        ],
        "resources": [],
        "course_module": "COMP101",
        "course_presentation": "2024A",
        "strategy": "balanced",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_active_at": datetime.now(timezone.utc).isoformat(),
        "member_count": 3,
    }
]


async def seed():
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB", "education-system")
    client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=8000)
    db = client[db_name]

    existing = await db.study_groups.count_documents({})
    if existing == 0:
        res = await db.study_groups.insert_many(SAMPLE_STUDY_GROUPS)
        print(f"Inserted {len(res.inserted_ids)} sample study groups into MongoDB study_groups collection.")
    else:
        print(f"Collection study_groups already has {existing} records.")


if __name__ == "__main__":
    asyncio.run(seed())
