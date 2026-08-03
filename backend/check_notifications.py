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

    print("Checking notifications...")
    cursor = db["notifications"].find({}).limit(20)
    async for notif in cursor:
        print(f"ID: {notif.get('_id')}")
        print(f"  Title: {notif.get('title')}")
        print(f"  Content: {notif.get('content')}")
        print(f"  Type: {notif.get('type')}")
        print("---")
        
    print(f"Total count: {await db['notifications'].count_documents({})}")
    print(f"Count with empty title: {await db['notifications'].count_documents({'title': {'$in': [None, '', ' ']}})}")
    print(f"Count with empty content: {await db['notifications'].count_documents({'content': {'$in': [None, '', ' ']}})}")

    client.close()

asyncio.run(main())