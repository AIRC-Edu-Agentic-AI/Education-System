import os
import sqlite3
import unittest

from db.analytics_db import initialize_analytics_db, ingest_event, get_analytics_summary, get_daily_trends, run_etl_from_jsonl


class AnalyticsDbTests(unittest.IsolatedAsyncioTestCase):
    async def test_initialize_and_ingest_event(self):
        db_path = os.path.join(os.path.dirname(__file__), "..", "uploads", "test_analytics.db")
        jsonl_path = os.path.join(os.path.dirname(__file__), "..", "uploads", "test_events.jsonl")
        if os.path.exists(db_path):
            os.remove(db_path)
        if os.path.exists(jsonl_path):
            os.remove(jsonl_path)

        conn = initialize_analytics_db(db_path=db_path)
        self.assertIsInstance(conn, sqlite3.Connection)

        event = {
            "event_type": "notification_sent",
            "actor_id": "teacher_admin",
            "target_id": "CS101",
            "payload": {"course_code": "CS101"},
            "source": "teacher_notification",
            "created_at": "2026-07-31T00:00:00+00:00",
        }

        ingest_event(event, db_path=db_path)
        summary = get_analytics_summary(db_path=db_path, days=7)
        trends = get_daily_trends(db_path=db_path, days=7)
        conn.close()

        self.assertGreater(summary["events_total"], 0)
        self.assertGreaterEqual(summary["top_event_types"][0]["count"], 1)
        self.assertEqual(summary["top_event_types"][0]["event_type"], "notification_sent")
        self.assertTrue(isinstance(trends, list))

        with open(jsonl_path, "w", encoding="utf-8") as handle:
            handle.write('{"event_type": "http_request", "created_at": "2026-07-31T00:00:00+00:00"}\n')
        result = run_etl_from_jsonl(jsonl_path=jsonl_path, db_path=db_path)
        self.assertGreater(result["loaded"], 0)

        if os.path.exists(db_path):
            os.remove(db_path)
        if os.path.exists(jsonl_path):
            os.remove(jsonl_path)


if __name__ == "__main__":
    unittest.main()
