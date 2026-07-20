import asyncio, os, sys
sys.stdout.reconfigure(encoding='utf-8')
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def main():
    uri = os.getenv("MONGODB_URI", "")
    db_name = os.getenv("MONGODB_DB", "education-system")
    client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=10000)
    db = client[db_name]

    print("=== Bắt đầu tạo danh sách lớp ===")
    
    courses = await db["courses"].find({}).to_list(None)
    for c in courses:
        members = c.get("members", [])
        if not members:
            continue
            
        classes = []
        chunk_size = 50
        for i in range(0, len(members), chunk_size):
            chunk = members[i:i+chunk_size]
            class_num = (i // chunk_size) + 1
            class_name = f"Lớp {class_num:02d}"
            classes.append({
                "class_name": class_name,
                "members": chunk
            })
            
        await db["courses"].update_one(
            {"_id": c["_id"]},
            {"$set": {"classes": classes}}
        )
        print(f"Course {c.get('course_code')} {c.get('presentation')}: Tạo {len(classes)} lớp (tổng {len(members)} SV).")

    print("=== Hoàn tất tạo danh sách lớp ===")
    client.close()

asyncio.run(main())