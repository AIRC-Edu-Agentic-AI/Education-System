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

    count = await db["students"].count_documents({})
    print(f"Tổng số sinh viên trong bảng 'students': {count}")
    
    first = await db["students"].find_one()
    if first:
        print("Tài liệu đầu tiên:")
        print(first.get("student_id"), first.get("full_name"), first.get("email"))

    client.close()

asyncio.run(main())