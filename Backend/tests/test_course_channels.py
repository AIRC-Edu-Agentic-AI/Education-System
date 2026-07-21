import unittest

from db.course_communication.channel import get_course_channels
from db.course_communication.constants import CHANNEL_TYPE_ANNOUNCEMENT, CHANNEL_TYPE_DISCUSSION


class FakeCursor:
    def __init__(self, docs):
        self._docs = docs

    def sort(self, *_args, **_kwargs):
        return self

    async def to_list(self, length=20):
        return list(self._docs[:length])


class FakeCollection:
    def __init__(self):
        self.docs = []

    def find(self, query):
        course_code = query.get("course_code")
        return FakeCursor([
            doc for doc in self.docs
            if doc.get("course_code") == course_code and doc.get("status") != "deleted"
        ])

    async def insert_many(self, docs):
        self.docs.extend(docs)


class FakeDB:
    def __init__(self):
        self.channels = FakeCollection()


class CourseChannelsTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_course_channels_creates_default_channels_for_course(self):
        db = FakeDB()

        channels = await get_course_channels(db, "CS101")

        self.assertEqual(len(channels), 2)
        self.assertEqual({channel["type"] for channel in channels}, {CHANNEL_TYPE_ANNOUNCEMENT, CHANNEL_TYPE_DISCUSSION})


if __name__ == "__main__":
    unittest.main()
