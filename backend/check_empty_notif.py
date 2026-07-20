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

    print("Checking one empty notification...")
    notif = await db["notifications"].find_one({"title": {"$in": [None, ""]}})
    if notif:
        for k, v in notif.items():
            print(f"  {k}: {v}")

    client.close()

asyncio.run(main())