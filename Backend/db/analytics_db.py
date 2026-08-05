import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Optional

try:
    import psycopg
except Exception:  # pragma: no cover - optional dependency
    psycopg = None

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "uploads", "analytics.db")


def _get_connection(db_path: Optional[str] = None):
    dsn = os.getenv("ANALYTICS_POSTGRES_DSN")
    if dsn and psycopg is not None:
        conn = psycopg.connect(dsn)
        conn.autocommit = True
        return conn, "postgres"

    target_path = db_path or DEFAULT_DB_PATH
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    return conn, "sqlite"


def _ensure_schema(conn, backend: str) -> None:
    if backend == "postgres":
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS analytics_events (
                    id BIGSERIAL PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    actor_id TEXT,
                    target_id TEXT,
                    payload TEXT,
                    source TEXT,
                    created_at TEXT NOT NULL,
                    created_at_dt TEXT NOT NULL
                )
            """)
        return

    conn.execute("""
        CREATE TABLE IF NOT EXISTS analytics_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            actor_id TEXT,
            target_id TEXT,
            payload TEXT,
            source TEXT,
            created_at TEXT NOT NULL,
            created_at_dt TEXT NOT NULL
        )
    """)
    conn.commit()


def initialize_analytics_db(db_path: Optional[str] = None):
    """Create the analytics store. Uses PostgreSQL when DSN is configured; otherwise SQLite."""
    conn, backend = _get_connection(db_path=db_path)
    _ensure_schema(conn, backend)
    return conn


def ingest_event(event: dict[str, Any], db_path: Optional[str] = None) -> dict[str, Any]:
    """Store a single event into the analytics DB."""
    conn, backend = _get_connection(db_path=db_path)
    _ensure_schema(conn, backend)
    created_at = event.get("created_at") or datetime.now(timezone.utc).isoformat()
    created_at_dt = event.get("created_at_dt") or created_at

    if backend == "postgres":
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO analytics_events (
                    event_type, actor_id, target_id, payload, source, created_at, created_at_dt
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    event.get("event_type"),
                    event.get("actor_id"),
                    event.get("target_id"),
                    json.dumps(event.get("payload") or {}),
                    event.get("source"),
                    created_at,
                    str(created_at_dt),
                ),
            )
        conn.close()
        return {"stored": True}

    conn.execute(
        """
        INSERT INTO analytics_events (
            event_type, actor_id, target_id, payload, source, created_at, created_at_dt
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event.get("event_type"),
            event.get("actor_id"),
            event.get("target_id"),
            str(event.get("payload") or {}),
            event.get("source"),
            created_at,
            str(created_at_dt),
        ),
    )
    conn.commit()
    conn.close()
    return {"stored": True}


def get_analytics_summary(db_path: Optional[str] = None, days: int = 7) -> dict[str, Any]:
    """Return simple KPI summary for dashboard usage."""
    conn, backend = _get_connection(db_path=db_path)
    try:
        _ensure_schema(conn, backend)
        if backend == "postgres":
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT event_type, COUNT(*) AS count
                    FROM analytics_events
                    WHERE created_at::timestamp >= NOW() - INTERVAL '1 day' * %s
                    GROUP BY event_type
                    ORDER BY count DESC
                    """,
                    (days,),
                )
                rows = cur.fetchall()
                cur.execute("SELECT COUNT(*) AS count FROM analytics_events")
                total_rows = cur.fetchone()
            return {
                "events_total": total_rows[0],
                "top_event_types": [
                    {"event_type": row[0], "count": row[1]} for row in rows
                ],
            }

        rows = conn.execute(
            """
            SELECT event_type, COUNT(*) AS count
            FROM analytics_events
            WHERE datetime(created_at) >= datetime('now', ?)
            GROUP BY event_type
            ORDER BY count DESC
            """,
            (f'-{days} days',),
        ).fetchall()

        total_rows = conn.execute("SELECT COUNT(*) AS count FROM analytics_events").fetchone()
        return {
            "events_total": total_rows["count"],
            "top_event_types": [
                {"event_type": row["event_type"], "count": row["count"]} for row in rows
            ],
        }
    finally:
        conn.close()


def run_etl_from_jsonl(jsonl_path: Optional[str] = None, db_path: Optional[str] = None) -> dict[str, Any]:
    """Load raw event JSONL into the analytics DB for ETL-ready processing."""
    target_path = jsonl_path or os.path.join(os.path.dirname(__file__), "..", "uploads", "event_logs.jsonl")
    if not os.path.exists(target_path):
        return {"loaded": 0, "message": "No JSONL file found"}

    loaded = 0
    with open(target_path, "r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            ingest_event(event, db_path=db_path)
            loaded += 1

    return {"loaded": loaded, "message": "ETL completed"}


def get_daily_trends(db_path: Optional[str] = None, days: int = 7) -> list[dict[str, Any]]:
    """Return daily event counts for simple charting."""
    conn, backend = _get_connection(db_path=db_path)
    try:
        _ensure_schema(conn, backend)
        if backend == "postgres":
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT TO_CHAR(created_at::timestamp, 'YYYY-MM-DD') AS day, COUNT(*) AS count
                    FROM analytics_events
                    WHERE created_at::timestamp >= NOW() - INTERVAL '1 day' * %s
                    GROUP BY TO_CHAR(created_at::timestamp, 'YYYY-MM-DD')
                    ORDER BY day ASC
                    """,
                    (days,),
                )
                rows = cur.fetchall()
            return [{"day": row[0], "count": row[1]} for row in rows]

        rows = conn.execute(
            """
            SELECT substr(created_at, 1, 10) AS day, COUNT(*) AS count
            FROM analytics_events
            WHERE datetime(created_at) >= datetime('now', ?)
            GROUP BY substr(created_at, 1, 10)
            ORDER BY day ASC
            """,
            (f'-{days} days',),
        ).fetchall()
        return [{"day": row["day"], "count": row["count"]} for row in rows]
    finally:
        conn.close()
