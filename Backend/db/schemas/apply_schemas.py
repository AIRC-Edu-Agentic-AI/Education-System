"""
Apply MongoDB JSON Schema validation to all collections.

Run from backend/ directory with venv active:
    python db/schemas/apply_schemas.py

This script:
  1. Connects to MongoDB using MONGODB_URI from .env
  2. Creates missing collections
  3. Applies $jsonSchema validator to each collection
  4. Reports success/failure per collection

Safe to run multiple times (idempotent).
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

from motor.motor_asyncio import AsyncIOMotorClient
from db.schemas.definitions import ALL_SCHEMAS


async def apply_schemas():
    uri = os.getenv("MONGODB_URI", "")
    db_name = os.getenv("MONGODB_DB", "education-system")

    if not uri or "placeholder" in uri:
        print("[ERROR] MONGODB_URI not set or invalid in .env")
        sys.exit(1)

    print(f"[INFO] Connecting to MongoDB... (db={db_name})")
    client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=10000)
    try:
        await client.admin.command("ping")
        print("[INFO] Connected successfully")
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        sys.exit(1)

    db = client[db_name]
    existing = await db.list_collection_names()
    print(f"[INFO] Existing collections: {len(existing)}")

    results = {"success": [], "failed": []}

    for collection_name, schema in ALL_SCHEMAS.items():
        try:
            if collection_name not in existing:
                await db.create_collection(collection_name)
                print(f"  [CREATED] {collection_name}")

            await db.command(
                "collMod",
                collection_name,
                validator=schema,
                validationLevel="moderate",   # moderate = validate only new/updated docs
                validationAction="warn",       # warn = log violations, do NOT reject
            )
            print(f"  [OK] {collection_name}")
            results["success"].append(collection_name)
        except Exception as e:
            print(f"  [FAIL] {collection_name}: {e}")
            results["failed"].append(collection_name)

    print(f"\n[DONE] {len(results['success'])} OK, {len(results['failed'])} FAILED")
    if results["failed"]:
        print(f"       Failed: {results['failed']}")
    client.close()


if __name__ == "__main__":
    asyncio.run(apply_schemas())
