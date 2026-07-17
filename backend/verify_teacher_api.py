import asyncio
import os
import json
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from db.mongodb import db_state
from routers.teacher_dashboard import list_courses
from routers.teacher_schedule import list_schedules

load_dotenv()
uri = os.getenv('MONGODB_URI')
db_name = os.getenv('MONGODB_DB', 'education-system')

async def main():
    client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=4000)
    await client.admin.command('ping')
    db_state['db'] = client[db_name]
    db_state['connected'] = True
    courses = await list_courses()
    schedules = await list_schedules()
    print('COURSES_OK', json.dumps(courses['courses'][:2], ensure_ascii=False))
    print('SCHEDULES_OK', json.dumps(schedules['schedules'][:2], ensure_ascii=False))
    client.close()

asyncio.run(main())
