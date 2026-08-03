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

    print("Checking processed_students...")
    doc = await db["processed_students"].find_one({"code_module": "BBB", "code_presentation": "2013B"})
    if doc:
        print("Keys:", doc.keys())
        print("group/class fields:", [k for k in doc.keys() if "group" in k.lower() or "class" in k.lower()])

    client.close()

asyncio.run(main())