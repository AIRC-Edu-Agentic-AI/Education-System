import os
import asyncio
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()
uri = os.getenv('MONGODB_URI')
db_name = os.getenv('MONGODB_DB', 'education-system')
print('URI present:', bool(uri))
print('DB name:', db_name)

async def main():
    client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=4000)
    try:
        await client.admin.command('ping')
        print('PING_OK')
        db = client[db_name]
        names = await db.list_collection_names()
        print('COLLECTIONS', names[:20])
    except Exception as e:
        print('ERR', repr(e))
    finally:
        client.close()

asyncio.run(main())
