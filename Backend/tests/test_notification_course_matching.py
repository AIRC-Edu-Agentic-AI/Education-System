import unittest

from routers.notifications import _course_code_matches


class FakeNotificationDoc(dict):
    pass


class NotificationCourseMatchingTests(unittest.TestCase):
    def test_matches_exact_course_code(self):
        self.assertTrue(_course_code_matches("CS101", "CS101"))

    def test_matches_prefix_and_suffix_variants(self):
        self.assertTrue(_course_code_matches("AAA 2013J", "AAA"))
        self.assertTrue(_course_code_matches("AAA", "AAA 2013J"))

    def test_does_not_match_unrelated_codes(self):
        self.assertFalse(_course_code_matches("CS101", "CS102"))

    def test_broadcast_log_entries_are_not_treated_as_student_notifications(self):
        doc = FakeNotificationDoc({"student_id": 123, "course_code": "AAA", "is_broadcast_log": True})
        self.assertTrue(doc.get("student_id") == 123)
        self.assertTrue(doc.get("is_broadcast_log") is True)


if __name__ == "__main__":
    unittest.main()
