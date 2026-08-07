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
