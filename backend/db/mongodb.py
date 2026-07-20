from motor.motor_asyncio import AsyncIOMotorClient
import os

db_state = {"connected": False, "client": None, "db": None}

async def connect_db():
    uri = os.getenv("MONGODB_URI", "")
    db_name = os.getenv("MONGODB_DB", "student_agent_db")
    use_mock = os.getenv("USE_MOCK_DATA", "true").strip().lower() == "true"

    if use_mock:
        print("[DB] USE_MOCK_DATA=true -> running in mock mode (no MongoDB)")
        db_state["connected"] = False
        return

    if not uri or "placeholder" in uri:
        print("[DB] MONGODB_URI missing or placeholder -> mock mode")
        db_state["connected"] = False
        return

    print(f"[DB] Connecting to MongoDB... (db={db_name})")
    try:
        client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=8000)
        await client.admin.command("ping")
        db_state["client"] = client
        db_state["db"] = client[db_name]
        db_state["connected"] = True
        print(f"[DB] Connected to MongoDB Atlas -> {db_name}")
    except Exception as e:
        print(f"[DB] Connection FAILED: {e}")
        print("[DB] Falling back to mock mode")
        db_state["connected"] = False


async def close_db():
    if db_state["client"]:
        db_state["client"].close()
        print("[DB] MongoDB connection closed")


def get_db():
    return db_state["db"] if db_state["connected"] else None
