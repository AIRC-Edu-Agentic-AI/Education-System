from motor.motor_asyncio import AsyncIOMotorClient
import os

db_state = {"connected": False, "client": None, "db": None}

async def connect_db():
    uri = os.getenv("MONGODB_URI", "")
    db_name = os.getenv("MONGODB_DB", "student_agent_db")
    use_mock = os.getenv("USE_MOCK_DATA", "true") == "true"

    if use_mock or not uri or "placeholder" in uri:
        print("[DB] Running in mock mode — MongoDB not connected")
        db_state["connected"] = False
        return

    try:
        client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=4000)
        await client.admin.command("ping")
        db_state["client"] = client
        db_state["db"] = client[db_name]
        db_state["connected"] = True
        print(f"[DB] Connected to MongoDB Atlas — {db_name}")
    except Exception as e:
        print(f"[DB] Connection failed ({e}) — falling back to mock data")
        db_state["connected"] = False


async def close_db():
    if db_state["client"]:
        db_state["client"].close()


def get_db():
    return db_state["db"] if db_state["connected"] else None
