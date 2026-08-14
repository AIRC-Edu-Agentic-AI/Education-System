from motor.motor_asyncio import AsyncIOMotorClient
import os

db_state = {"connected": False, "client": None, "db": None}

async def connect_db():
    uri = os.getenv("MONGODB_URI", "")
    db_name = os.getenv("MONGODB_DB", "student_agent_db")
    use_mock = os.getenv("USE_MOCK_DATA", "true").strip().lower() == "true"

    # Debug: print minimal info about environment (do not leak credentials)
    try:
        uri_set = bool(uri)
        contains_placeholder = "placeholder" in uri.lower()
    except Exception:
        uri_set = False
        contains_placeholder = False
    print(f"[DB] ENV DEBUG -> USE_MOCK_DATA={use_mock}, MONGODB_URI_set={uri_set}, MONGODB_URI_contains_placeholder={contains_placeholder}, MONGODB_DB={db_name}")

    if use_mock:
        print("[DB] USE_MOCK_DATA=true -> running in mock mode (no MongoDB)")
        db_state["connected"] = False
        return

    if not uri or "placeholder" in uri.lower():
        print("[DB] MONGODB_URI missing or placeholder -> mock mode")
        db_state["connected"] = False
        return

    print(f"[DB] Connecting to MongoDB... (db={db_name})")
    try:
        client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=8000)
        await client.admin.command("ping")
        db = client[db_name]
        db_state["client"] = client
        db_state["db"] = db
        db_state["connected"] = True
        print(f"[DB] Connected to MongoDB Atlas -> {db_name}")

        # Create essential performance indexes in the background
        import asyncio
        asyncio.create_task(_ensure_indexes(db))
    except Exception as e:
        print(f"[DB] Connection FAILED: {e}")
        print("[DB] Falling back to mock mode")
        db_state["connected"] = False


async def _ensure_indexes(db):
    try:
        # Index students for course filtering and ID lookups
        await db["students"].create_index([("enrollments.code_module", 1), ("enrollments.code_presentation", 1)], background=True)
        await db["students"].create_index([("student_id", 1)], background=True)
        await db["students"].create_index([("risk.tier", 1)], background=True)

        # Index courses
        await db["courses"].create_index([("code_module", 1), ("code_presentation", 1)], background=True)

        # Index notifications for system inbox and recipient queries
        await db["notifications"].create_index([("course_code", 1), ("createdAt", -1)], background=True)
        await db["notifications"].create_index([("recipient_id", 1), ("createdAt", -1)], background=True)
        await db["notifications"].create_index([("student_id", 1)], background=True)

        # Index channels and messages
        await db["channels"].create_index([("course_code", 1), ("type", 1)], background=True)
        await db["channels"].create_index([("members", 1)], background=True)
        await db["messages"].create_index([("channel_id", 1), ("created_at", 1)], background=True)

        # Index study groups and classrooms
        await db["study_groups"].create_index([("course_code", 1)], background=True)
        await db["classrooms"].create_index([("course_code", 1)], background=True)
        print("[DB] All performance indexes verified and ready.")
    except Exception as e:
        print(f"[DB] Index creation warning: {e}")


async def close_db():
    if db_state["client"]:
        db_state["client"].close()
        print("[DB] MongoDB connection closed")


def get_db():
    return db_state["db"] if db_state["connected"] else None
