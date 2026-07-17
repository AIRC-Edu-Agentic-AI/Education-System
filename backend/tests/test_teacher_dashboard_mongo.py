from routers.teacher_dashboard import _course_payload


def test_course_payload_reads_mongo_course_fields():
    course = {
        "course_code": "DATA201",
        "title": "Phân tích Dữ liệu & Thống kê",
        "presentation": "2024A",
        "term": "2024A",
        "members": [28400, 28401, 28402],
    }

    payload = _course_payload(course)

    assert payload["module"] == "DATA201"
    assert payload["module_name"] == "Phân tích Dữ liệu & Thống kê"
    assert payload["presentation"] == "2024A"
    assert payload["presentation_name"] == "2024A"
    assert payload["student_count"] == 3
