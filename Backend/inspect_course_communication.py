import asyncio
import os
from dotenv import load_dotenv
load_dotenv()
from db.mongodb import connect_db, db_state

async def main():
    await connect_db()
    print('connected', db_state['connected'])
    if not db_state['db']:
        return
    db = db_state['db']
    for name in ['courses', 'channels', 'messages', 'students']:
        try:
            print(name, await db[name].count_documents({}))
        except Exception as e:
            print(name, 'ERR', e)
    print('sample course', await db.courses.find_one())
    print('sample channel', await db.channels.find_one())
    print('sample message', await db.messages.find_one())

asyncio.run(main())
