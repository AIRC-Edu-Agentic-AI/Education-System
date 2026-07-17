"""One-time maintenance script: ensure announcement/discussion channels exist for all courses.

Run from the `backend/` folder with the project venv active:

    python scripts/ensure_channels.py

It reads MONGODB_URI and MONGODB_DB from .env or environment.
"""
import asyncio
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI", "")
MONGODB_DB = os.getenv("MONGODB_DB", "student_agent_db")

if not MONGODB_URI or "placeholder" in MONGODB_URI:
    print("MONGODB_URI not set or is placeholder. Set .env and try again.")
    raise SystemExit(1)

async def main():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[MONGODB_DB]

    # import the helper from the package
    from db import course_communication

    courses = await db.courses.find({}).to_list(length=1000)
    print(f"Found {len(courses)} courses. Ensuring channels...")
    changed = 0
    for c in courses:
        code = c.get("course_code")
        if not code:
            continue
        before = await db.channels.count_documents({"course_code": code, "status": {"$ne": "deleted"}})
        await course_communication._ensure_course_channels(db, code)
        after = await db.channels.count_documents({"course_code": code, "status": {"$ne": "deleted"}})
        if after > before:
            print(f"  Created {after-before} channels for {code}")
            changed += 1
    print(f"Done. Updated channels for {changed} courses.")
    client.close()

if __name__ == '__main__':
    asyncio.run(main())
