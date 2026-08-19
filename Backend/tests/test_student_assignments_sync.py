from unittest.mock import AsyncMock, patch

from routers.assignment.teacher import _notify_assignment_recipients
from routers.student import _build_assessment_payload


def test_build_assessment_payload_uses_assignments_collection():
    payload = _build_assessment_payload(
        {
            "id_assessment": 101,
            "code_module": "CS101",
            "code_presentation": "2024A",
            "title": "Assignment 1",
            "type": "TMA",
            "due_date": 1735689600,
            "weight": 15.0,
            "status": "active",
        },
        "CS101",
        "2024A",
        {
            "student_id": 7,
            "id_assessment": 101,
            "status": "submitted",
            "submitted_at": "2024-01-01T00:00:00",
            "score": 88.5,
        },
    )

    assert payload["id_assessment"] == 101
    assert payload["code_module"] == "CS101"
    assert payload["due_date"] == 1735689600
    assert payload["submitted_date"] is not None
    assert payload["score"] == 88.5


async def test_assignment_notification_targets_unique_students():
    class NotificationCollection:
        def __init__(self):
            self.docs = []

        async def insert_one(self, doc):
            self.docs.append(doc)

    class FakeDB(dict):
        def __init__(self):
            super().__init__()
            self["notifications"] = NotificationCollection()

    db = FakeDB()
    send_to_user = AsyncMock()
    manager = type("Manager", (), {"send_to_user": send_to_user})()
    assignment = {
        "id_assessment": 101,
        "title": "Database Design",
        "due_date": 1760000000,
    }

    with patch("routers.realtime_chat.manager", manager):
        count = await _notify_assignment_recipients(
            db,
            [7, 7, "8", 9],
            assignment,
            "CS101 2026A",
        )

    assert count == 2
    assert [doc["student_id"] for doc in db["notifications"].docs] == [7, 9]
    assert db["notifications"].docs[0]["payload"]["title"] == "New Assignment Available"
    assert "Database Design has been assigned" in db["notifications"].docs[0]["payload"]["body"]
    assert send_to_user.await_count == 2
