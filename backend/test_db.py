import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient('mongodb://levinhkhanh:L7EfvMSPlP5oTKlJ@ac-nus8ysv-shard-00-00.tsrzoux.mongodb.net:27017,ac-nus8ysv-shard-00-01.tsrzoux.mongodb.net:27017,ac-nus8ysv-shard-00-02.tsrzoux.mongodb.net:27017/?ssl=true&replicaSet=atlas-1398m4-shard-0&authSource=admin&appName=OuladCluster')
db = client['education-system']

async def check():
    count = await db['notifications'].count_documents({'type': 'general', 'payload.title': 'New Class Scheduled'})
    print(f'Found {count} notifications with title New Class Scheduled')
    
    # Also check if any schedules have been saved today
    scheds = await db['schedules'].find_one({})
    if scheds and 'schedules' in scheds:
        print(f"Total schedules in DB: {len(scheds['schedules'])}")
    else:
        print("No schedules in DB or different format")

if __name__ == "__main__":
    asyncio.run(check())
