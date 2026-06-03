from datetime import datetime, timedelta, timezone

MOCK_STUDENT = {
    "_id": "mock_student_001",
    "auth0_id": "auth0|mock_student_001",
    "student_id": 28400,
    "full_name": "Nguyễn Văn An",
    "short_name": "Văn An",
    "demographics": {
        "gender": "M",
        "age_band": "25-35",
        "region": "Hà Nội",
        "highest_education": "HE Qualification",
        "imd_band": "20-30%",
        "disability": False,
        "num_prev_attempts": 0,
        "studied_credits": 60,
    },
    "enrollments": [
        {
            "code_module": "DATA201",
            "code_presentation": "2024A",
            "title": "Phân tích Dữ liệu & Thống kê",
            "module_length": 30,
            "registration_date": -15,
            "unregistration_date": None,
            "final_result": None,
            "assessments": [
                {"id_assessment": 1752, "type": "TMA", "due_date": 19,
                 "weight": 10, "score": 42, "submitted_date": 18, "is_banked": False},
                {"id_assessment": 1753, "type": "TMA", "due_date": 49,
                 "weight": 25, "score": None, "submitted_date": None, "is_banked": False},
                {"id_assessment": 1754, "type": "CMA", "due_date": 68,
                 "weight": 15, "score": None, "submitted_date": None, "is_banked": False},
                {"id_assessment": 1755, "type": "Exam", "due_date": 261,
                 "weight": 50, "score": None, "submitted_date": None, "is_banked": False},
            ],
            "vle_summary": {
                "total_clicks": 3842,
                "last_active_day": 42,
                "by_activity_type": {
                    "resource": 1240, "forumng": 287,
                    "oucontent": 1100, "quiz": 420,
                    "url": 312, "homepage": 483,
                },
                "weekly_clicks": [320, 410, 380, 300, 210, 120, 45, *([0] * 23)],
            },
        },
        {
            "code_module": "MATH102",
            "code_presentation": "2024A",
            "title": "Đại số Tuyến tính",
            "module_length": 30,
            "registration_date": -15,
            "unregistration_date": None,
            "final_result": None,
            "assessments": [
                {"id_assessment": 2010, "type": "TMA", "due_date": 22,
                 "weight": 20, "score": 65, "submitted_date": 21, "is_banked": False},
                {"id_assessment": 2011, "type": "CMA", "due_date": 55,
                 "weight": 30, "score": 58, "submitted_date": 54, "is_banked": False},
                {"id_assessment": 2012, "type": "Exam", "due_date": 250,
                 "weight": 50, "score": None, "submitted_date": None, "is_banked": False},
            ],
            "vle_summary": {
                "total_clicks": 2110,
                "last_active_day": 45,
                "by_activity_type": {
                    "resource": 720, "oucontent": 640, "quiz": 410, "homepage": 340,
                },
                "weekly_clicks": [180, 220, 240, 210, 190, 160, 140, *([0] * 23)],
            },
        },
        {
            "code_module": "COMP101",
            "code_presentation": "2024A",
            "title": "Lập trình Python",
            "module_length": 30,
            "registration_date": -15,
            "unregistration_date": None,
            "final_result": None,
            "assessments": [
                {"id_assessment": 3010, "type": "TMA", "due_date": 20,
                 "weight": 15, "score": 88, "submitted_date": 19, "is_banked": False},
                {"id_assessment": 3011, "type": "TMA", "due_date": 48,
                 "weight": 25, "score": 79, "submitted_date": 47, "is_banked": False},
                {"id_assessment": 3012, "type": "Exam", "due_date": 255,
                 "weight": 60, "score": None, "submitted_date": None, "is_banked": False},
            ],
            "vle_summary": {
                "total_clicks": 5240,
                "last_active_day": 46,
                "by_activity_type": {
                    "resource": 1480, "oucontent": 1620, "quiz": 1100,
                    "forumng": 540, "homepage": 500,
                },
                "weekly_clicks": [410, 460, 520, 480, 500, 470, 510, *([0] * 23)],
            },
        },
        {
            "code_module": "STAT110",
            "code_presentation": "2024A",
            "title": "Xác suất & Thống kê Suy luận",
            "module_length": 30,
            "registration_date": -15,
            "unregistration_date": None,
            "final_result": None,
            "assessments": [
                {"id_assessment": 4010, "type": "TMA", "due_date": 25,
                 "weight": 20, "score": 71, "submitted_date": 24, "is_banked": False},
                {"id_assessment": 4011, "type": "CMA", "due_date": 60,
                 "weight": 20, "score": None, "submitted_date": None, "is_banked": False},
                {"id_assessment": 4012, "type": "Exam", "due_date": 258,
                 "weight": 60, "score": None, "submitted_date": None, "is_banked": False},
            ],
            "vle_summary": {
                "total_clicks": 2980,
                "last_active_day": 44,
                "by_activity_type": {
                    "resource": 980, "oucontent": 870, "quiz": 620, "homepage": 510,
                },
                "weekly_clicks": [260, 300, 280, 310, 270, 240, 230, *([0] * 23)],
            },
        },
    ],
    "risk": {
        "tier": 3,
        "score": 0.82,
        "flags": ["low_vle_engagement", "assessment_due_soon", "assessment_shock"],
        "computed_at": datetime.now(timezone.utc).isoformat(),
    },
    "prerequisite_gaps": ["Thống kê cơ bản", "Đại số tuyến tính"],
    "updated_at": datetime.now(timezone.utc).isoformat(),
}

MOCK_SCHEDULE = {
    "current_week": 7,
    "total_weeks": 30,
    "streak_days": 12,
    "lectures": [
        {"title": "Phân tích Dữ liệu & Thống kê", "subtitle": "Thứ 2, 08:00",
         "is_completed": False, "is_urgent": False},
        {"title": "Đại số Tuyến tính", "subtitle": "Thứ 4, 10:00",
         "is_completed": False, "is_urgent": False},
        {"title": "Kiểm định giả thuyết", "subtitle": "Thứ 6, 14:00",
         "is_completed": False, "is_urgent": False},
    ],
    "classes": [
        {"title": "Lab Lập trình Python", "subtitle": "Thứ 3, 13:00 · Phòng B204",
         "is_completed": False, "is_urgent": False},
        {"title": "Xác suất & Thống kê Suy luận", "subtitle": "Thứ 5, 09:00 · Online",
         "is_completed": False, "is_urgent": False},
    ],
    "assignments": [
        {"title": "TMA-02 — Phân tích hồi quy", "subtitle": "Nộp trước Thứ 6",
         "is_completed": False, "is_urgent": True},
        {"title": "CMA-01 — Quiz chương 3", "subtitle": "Nộp trước Thứ 7",
         "is_completed": False, "is_urgent": False},
    ],
    "exams": [],
}

# Weekly risk snapshots — rising trend that explains why interventions fired.
# Aligned to weeks 1–7 (current week). Pair with declining VLE clicks.
MOCK_RISK_HISTORY = {
    "student_id": 28400,
    "entries": [
        {"week": 1, "score": 0.30, "tier": 1},
        {"week": 2, "score": 0.38, "tier": 1},
        {"week": 3, "score": 0.46, "tier": 2},
        {"week": 4, "score": 0.55, "tier": 2},
        {"week": 5, "score": 0.66, "tier": 2},
        {"week": 6, "score": 0.74, "tier": 3},
        {"week": 7, "score": 0.82, "tier": 3},
    ],
}

MOCK_NEXT_COURSES = [
    {
        "code": "DATA305",
        "title": "Trực quan hoá Dữ liệu",
        "prerequisites": [],
        "description": "Kể chuyện bằng dữ liệu với matplotlib, seaborn và Plotly",
    },
    {
        "code": "STAT320",
        "title": "Thống kê Ứng dụng Nâng cao",
        "prerequisites": ["Thống kê cơ bản", "Đại số tuyến tính"],
        "description": "Phân tích dữ liệu nâng cao với R và Python",
    },
    {
        "code": "ML340",
        "title": "Nhập môn Học máy",
        "prerequisites": ["Hồi quy tuyến tính", "Đại số tuyến tính"],
        "description": "Giới thiệu machine learning với scikit-learn",
    },
    {
        "code": "DATA310",
        "title": "Phân tích Dữ liệu Thực hành",
        "prerequisites": ["Thống kê cơ bản"],
        "description": "Dự án thực tế với pandas, matplotlib, seaborn",
    },
]

MOCK_MILESTONES = [
    {
        "_id": "ms_001",
        "student_id": 28400,
        "id_assessment": 1753,
        "module": "BBB",
        "title": "TMA-02 — Phân tích hồi quy",
        "milestones": [
            {"id": "m1", "title": "Đọc đề bài & tài liệu tham khảo", "status": "done", "due_offset_days": -14},
            {"id": "m2", "title": "Phân tích dữ liệu ban đầu", "status": "in_progress", "due_offset_days": -7},
            {"id": "m3", "title": "Viết báo cáo nháp", "status": "pending", "due_offset_days": -3},
            {"id": "m4", "title": "Nộp bài chính thức", "status": "pending", "due_offset_days": 0},
        ],
        "created_at": "2025-01-15T08:00:00",
    }
]

MOCK_KNOWLEDGE_STATES = {
    "student_id": 28400,
    "states": {
        "Thống kê cơ bản": {
            "mastery": 0.35, "last_updated": "2025-01-10", "evidence_count": 2
        },
        "Đại số tuyến tính": {
            "mastery": 0.28, "last_updated": "2025-01-12", "evidence_count": 1
        },
        "Hồi quy tuyến tính": {
            "mastery": 0.55, "last_updated": "2025-01-18", "evidence_count": 3
        },
        "Kiểm định giả thuyết": {
            "mastery": 0.42, "last_updated": "2025-01-20", "evidence_count": 2
        },
    },
}

MOCK_NOTIFICATIONS = [
    {
        "_id": "notif_001",
        "student_id": 28400,
        "type": "deadline_warning",
        "payload": {
            "title": "TMA-02 — Phân tích Dữ liệu sắp đến hạn",
            "body": "Còn 3 ngày (đến ngày 49). Hãy bắt đầu sớm.",
        },
        "action_options": [
            {
                "label": "Lên kế hoạch",
                "action": "open_chat",
                "payload": {"message": "Giúp tôi lên kế hoạch hoàn thành TMA-02 môn Phân tích Dữ liệu"},
            },
            {"label": "Nhắc lại sau", "action": "snooze", "payload": {}},
        ],
        "read": False,
        "created_at": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
    },
    {
        "_id": "notif_002",
        "student_id": 28400,
        "type": "reminder",
        "payload": {
            "title": "Ôn tập hôm nay",
            "body": "Bạn có 4 thẻ flashcard cần ôn tập theo lịch SM-2.",
        },
        "action_options": [
            {
                "label": "Hỏi trợ lý",
                "action": "open_chat",
                "payload": {"message": "Hôm nay tôi nên ôn tập gì?"},
            },
        ],
        "read": False,
        "created_at": (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat(),
    },
]

MOCK_STUDY_PLAN = [
    {"subject": "Ôn tập Tuần 6 — Phân tích Dữ liệu", "type": "review",
     "duration": 45, "day": "Thứ 2", "time": "19:00", "sm2_interval": 3},
    {"subject": "Đọc tài liệu Tuần 7", "type": "new",
     "duration": 60, "day": "Thứ 3", "time": "20:00", "sm2_interval": None},
    {"subject": "Luyện tập TMA-02", "type": "practice",
     "duration": 90, "day": "Thứ 4", "time": "19:30", "sm2_interval": None},
    {"subject": "Flashcard Tuần 5–6", "type": "spaced_rep",
     "duration": 20, "day": "Thứ 5", "time": "08:00", "sm2_interval": 7},
    {"subject": "Hoàn thiện TMA-02", "type": "assignment",
     "duration": 120, "day": "Thứ 6", "time": "19:00", "sm2_interval": None},
]

MOCK_RESOURCES = [
    {"title": "Slide Tuần 7 — Kiểm định giả thuyết", "module": "DATA201",
     "type": "slide", "url": "#", "bookmarked": True},
    {"title": "Tài liệu đọc thêm — Hồi quy tuyến tính", "module": "DATA201",
     "type": "document", "url": "#", "bookmarked": False},
    {"title": "Video hướng dẫn Python pandas", "module": "COMP101",
     "type": "video", "url": "#", "bookmarked": True},
    {"title": "Quiz tự luyện — Đại số tuyến tính", "module": "MATH102",
     "type": "quiz", "url": "#", "bookmarked": False},
]
