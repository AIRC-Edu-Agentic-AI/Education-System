import unittest

from db.event_logging import log_event


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


if __name__ == "__main__":
    unittest.main()
