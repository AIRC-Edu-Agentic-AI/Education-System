import json
import os
from datetime import datetime, timezone
from typing import Any, Optional


DEFAULT_EVENT_LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "uploads", "event_logs.jsonl")

from db.analytics_db import ingest_event

EVENT_LOGS_COLLECTION = "event_logs"
EVENT_LOGS_FILE = DEFAULT_EVENT_LOG_PATH


async def log_event(
    db: Optional[Any],
    event_type: str,
    actor_id: Optional[str] = None,
    target_id: Optional[str] = None,
    payload: Optional[dict] = None,
    source: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> dict:
    """Persist a structured event for analytics, auditing, and ETL input."""
    now = datetime.now(timezone.utc)
    event_doc = {
        "event_type": event_type,
        "actor_id": actor_id,
        "target_id": target_id,
        "payload": payload or {},
        "source": source,
        "metadata": metadata or {},
        "created_at": now.isoformat(),
        "created_at_dt": now,
    }

    if db is not None and hasattr(db, "__contains__") and "event_logs" in db:
        result = await db[EVENT_LOGS_COLLECTION].insert_one(event_doc)
        event_doc["_id"] = result.inserted_id

    os.makedirs(os.path.dirname(EVENT_LOGS_FILE), exist_ok=True)
    with open(EVENT_LOGS_FILE, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(event_doc, default=str) + "\n")

    try:
        ingest_event(event_doc)
    except Exception:
        pass

    return event_doc


async def list_events(db: Any, limit: int = 100, event_type: Optional[str] = None) -> list[dict]:
    """Fetch recent events from MongoDB if available, otherwise read the JSONL file."""
    if db is not None and EVENT_LOGS_COLLECTION in db:
        query = {}
        if event_type:
            query["event_type"] = event_type
        cursor = db[EVENT_LOGS_COLLECTION].find(query).sort("created_at_dt", -1).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [
            {
                **doc,
                "_id": str(doc.get("_id")),
                "created_at_dt": doc.get("created_at_dt").isoformat() if doc.get("created_at_dt") else None,
            }
            for doc in docs
        ]

    if os.path.exists(EVENT_LOGS_FILE):
        with open(EVENT_LOGS_FILE, "r", encoding="utf-8") as handle:
            lines = [json.loads(line) for line in handle if line.strip()]
        if event_type:
            lines = [line for line in lines if line.get("event_type") == event_type]
        return lines[-limit:][::-1]

    return []
