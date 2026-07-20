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

    courses = {}
    async for s in db["students"].find({}):
        sid = s.get("student_id")
        for e in s.get("enrollments", []):
            k = (e.get("code_module"), e.get("code_presentation"))
            if k not in courses:
                courses[k] = {"title": e.get("title", ""), "members": []}
            courses[k]["members"].append(sid)
            
    print(f"Tổng số courses độc nhất: {len(courses)}")
    for k, v in list(courses.items())[:10]:
        print(f"  Module: {k[0]}, Pres: {k[1]}, Title: {v['title']}, Members: {len(v['members'])}")

    client.close()

asyncio.run(main())