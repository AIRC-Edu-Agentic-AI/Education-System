import json
import os
import unittest
from unittest.mock import patch

import bcrypt

from db.event_logging import log_event
from routers import auth as auth_router


class FakeCollection:
    def __init__(self):
        self.docs = []

    async def insert_one(self, doc):
        self.docs.append(doc)
        return type("Result", (), {"inserted_id": "fake-id"})()


class FakeDB(dict):
    def __init__(self):
        super().__init__()
        self["event_logs"] = FakeCollection()


class EventLoggingTests(unittest.IsolatedAsyncioTestCase):
    async def test_log_event_writes_to_collection(self):
        db = FakeDB()

        event = await log_event(
            db=db,
            event_type="notification_sent",
            actor_id="teacher_admin",
            payload={"course_code": "CS101"},
            source="teacher_notification",
        )

        self.assertEqual(event["event_type"], "notification_sent")
        self.assertEqual(db["event_logs"].docs[0]["event_type"], "notification_sent")
        self.assertEqual(db["event_logs"].docs[0]["actor_id"], "teacher_admin")

    async def test_log_event_writes_jsonl_when_db_is_none(self):
        log_path = os.path.join(os.path.dirname(__file__), "..", "uploads", "test_http_events.jsonl")
        if os.path.exists(log_path):
            os.remove(log_path)

        with patch("db.event_logging.EVENT_LOGS_FILE", log_path):
            event = await log_event(
                db=None,
                event_type="http_request",
                target_id="/student/28400",
                payload={"method": "GET", "status_code": 200},
                source="http_middleware",
            )

        self.assertEqual(event["event_type"], "http_request")
        self.assertTrue(os.path.exists(log_path))
        with open(log_path, "r", encoding="utf-8") as handle:
            lines = [json.loads(line) for line in handle if line.strip()]

        self.assertEqual(lines[-1]["event_type"], "http_request")
        self.assertEqual(lines[-1]["target_id"], "/student/28400")

        if os.path.exists(log_path):
            os.remove(log_path)

    async def test_login_success_emits_auth_event(self):
        calls = []

        async def fake_log_event(*args, **kwargs):
            calls.append((args, kwargs))
            return {"ok": True}

        class FakeCollection:
            async def find_one(self, query):
                if query.get("student_id") == 56507:
                    password_hash = bcrypt.hashpw(b"demo123", bcrypt.gensalt()).decode("utf-8")
                    return {"student_id": 56507, "password_hash": password_hash}
                return None

        class FakeDB(dict):
            def __init__(self):
                super().__init__()
                self["students"] = FakeCollection()

        with patch("routers.auth.log_event", side_effect=fake_log_event), \
             patch.object(auth_router, "db_state", {"connected": True, "db": FakeDB()}):
            response = await auth_router.login(auth_router.LoginRequest(student_id=57506, password="demo123"))

        self.assertEqual(response.student_id, 57506)
        self.assertTrue(any(len(call[0]) >= 2 and call[0][1] == "login_success" for call in calls))


if __name__ == "__main__":
    unittest.main()
