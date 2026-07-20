import asyncio, os, sys
from datetime import datetime, timezone
sys.stdout.reconfigure(encoding='utf-8')
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def main():
    uri = os.getenv("MONGODB_URI", "")
    db_name = os.getenv("MONGODB_DB", "education-system")
    client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=10000)
    db = client[db_name]

    print("=== Bắt đầu migration courses ===")
    
    courses_map = {} # (module, presentation) -> dict
    
    print("Loading students and enrollments...")
    async for sdoc in db["students"].find({}, {"student_id": 1, "enrollments": 1}):
        sid = sdoc.get("student_id")
        if not sid: continue
        
        for e in sdoc.get("enrollments", []):
            mod = e.get("code_module")
            pres = e.get("code_presentation")
            title = e.get("title", "")
            
            if not mod or not pres: continue
            
            k = (mod, pres)
            if k not in courses_map:
                courses_map[k] = {
                    "course_code": mod,
                    "presentation": pres,
                    "title": title or mod,
                    "term": pres,
                    "instructors": [1001],
                    "class_reps": [],
                    "members": set(),
                    "status": "active",
                    "settings": {
                        "notification_window": {"start": "08:00", "end": "18:00"},
                        "mentions_only": False,
                        "mute_discussion": False
                    },
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            courses_map[k]["members"].add(sid)

    # Optional: fetch full module titles from processed_courses if available
    print("Enhancing titles from processed_courses...")
    async for pc in db["processed_courses"].find({}):
        mod = pc.get("module")
        pres = pc.get("presentation")
        k = (mod, pres)
        if k in courses_map:
            if pc.get("module_name"):
                courses_map[k]["title"] = pc.get("module_name")

    # Optional: handle custom titles (e.g. CS01)
    for k, c in courses_map.items():
        if k[0] == "CS01": c["title"] = "Cơ sở dữ liệu"
        elif k[0] == "Cs01": c["title"] = "Cấu trúc dữ liệu"
        elif k[0] == "Css01": c["title"] = "Kỹ thuật phần mềm"
        elif k[0] == "Data 1": c["title"] = "Khai phá dữ liệu"

    print(f"Tổng số courses cần lưu: {len(courses_map)}")
    
    # Save to courses collection
    print("Đang lưu vào DB (bảng courses)...")
    operations = []
    from pymongo import UpdateOne
    for k, cdoc in courses_map.items():
        # Convert members set to list
        cdoc["members"] = list(cdoc["members"])
        operations.append(UpdateOne(
            {"course_code": cdoc["course_code"], "presentation": cdoc["presentation"]},
            {"$set": cdoc},
            upsert=True
        ))
    
    if operations:
        result = await db["courses"].bulk_write(operations)
        print(f"  Inserted/Updated {len(operations)} courses")
        
    print("=== Hoàn tất migration courses ===")
    client.close()

asyncio.run(main())