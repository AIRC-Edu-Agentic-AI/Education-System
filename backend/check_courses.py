import asyncio, os, sys, json
sys.stdout.reconfigure(encoding='utf-8')
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def main():
    uri = os.getenv("MONGODB_URI", "")
    db_name = os.getenv("MONGODB_DB", "education-system")
    client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=10000)
    db = client[db_name]

    print("=== courses (1 doc) ===")
    c = await db["courses"].find_one({})
    if c:
        for k, v in c.items():
            print(f"  {k}: {type(v).__name__} = {str(v)[:100]}")
    
    print("\n=== processed_courses (1 doc) ===")
    pc = await db["processed_courses"].find_one({})
    if pc:
        for k, v in pc.items():
            print(f"  {k}: {type(v).__name__} = {str(v)[:100]}")

    print("\nCounts:")
    print(f"  courses: {await db['courses'].count_documents({})}")
    print(f"  processed_courses: {await db['processed_courses'].count_documents({})}")

    client.close()

asyncio.run(main())