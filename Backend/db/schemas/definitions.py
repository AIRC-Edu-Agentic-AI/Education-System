"""
MongoDB JSON Schema validation definitions.
Generated from the system specification document.

Collections covered (15):
  students, courses, classrooms,
  timetable_blocks, study_plans,
  assignments, submissions, assignment_milestones,
  notifications, channels, messages,
  knowledge_states, risk_history, agent_logs,
  resources, audit_logs
"""

STUDENTS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "title": "students",
        "required": ["student_id", "auth0_id", "full_name", "email", "role", "risk", "created_at", "updated_at"],
        "properties": {
            "_id":          {"bsonType": "objectId"},
            "student_id":   {"bsonType": "int", "description": "Ma dinh danh noi bo sinh vien"},
            "auth0_id":     {"bsonType": "string"},
            "full_name":    {"bsonType": "string"},
            "short_name":   {"bsonType": "string"},
            "email":        {"bsonType": "string", "pattern": "^.+@.+\\..+$"},
            "password_hash": {"bsonType": "string"},
            "role":         {"enum": ["student", "teacher", "admin"]},
            "is_active":    {"bsonType": "bool"},
            "avatar_url":   {"bsonType": ["string", "null"]},
            "demographics": {
                "bsonType": "object",
                "properties": {
                    "gender":             {"bsonType": "string"},
                    "age_band":           {"bsonType": "string"},
                    "region":             {"bsonType": "string"},
                    "highest_education":  {"bsonType": "string"},
                    "imd_band":           {"bsonType": "string"},
                    "disability":         {"bsonType": ["bool", "string"]},
                    "num_prev_attempts":  {"bsonType": "int"},
                    "studied_credits":    {"bsonType": "int"},
                },
            },
            "risk": {
                "bsonType": "object",
                "required": ["score", "tier", "flags", "computed_at"],
                "properties": {
                    "score":       {"bsonType": ["double", "int"], "minimum": 0, "maximum": 1},
                    "tier":        {"bsonType": "int", "minimum": 1, "maximum": 4},
                    "flags":       {"bsonType": "array", "items": {"bsonType": "string"}},
                    "computed_at": {"bsonType": ["date", "string"]},
                },
            },
            "enrollments": {
                "bsonType": "array",
                "items": {
                    "bsonType": "object",
                    "properties": {
                        "code_module":         {"bsonType": "string"},
                        "code_presentation":   {"bsonType": "string"},
                        "title":               {"bsonType": "string"},
                        "module_length":       {"bsonType": ["int", "null"]},
                        "registration_date":   {"bsonType": ["date", "int", "string", "null"]},
                        "unregistration_date": {"bsonType": ["date", "string", "null"]},
                        "final_result":        {"bsonType": ["string", "null"]},
                        "vle_summary":         {"bsonType": ["object", "null"]},
                    },
                },
            },
            "created_at": {"bsonType": ["date", "string"]},
            "updated_at": {"bsonType": ["date", "string"]},
        },
    }
}

COURSES_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "title": "courses",
        "required": ["code_module", "presentation", "title", "term", "module_length", "created_at", "updated_at"],
        "properties": {
            "_id":           {"bsonType": "objectId"},
            "code_module":   {"bsonType": "string", "description": "Ma mon hoc (VD: DATA201, AAA)"},
            "presentation":  {"bsonType": "string"},
            "title":         {"bsonType": "string"},
            "term":          {"bsonType": "string"},
            "instructors":   {"bsonType": "array", "items": {"bsonType": ["int", "string"]}},
            "class_reps":    {"bsonType": "array", "items": {"bsonType": ["int", "string"]}},
            "members":       {"bsonType": "array", "items": {"bsonType": ["int", "string"]}},
            "module_length": {"bsonType": ["int", "null"]},
            "status":        {"enum": ["active", "archived", "deleted"]},
            "settings":      {"bsonType": "object"},
            "created_at":    {"bsonType": ["date", "string"]},
            "updated_at":    {"bsonType": ["date", "string"]},
        },
    }
}

CLASSROOMS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "title": "classrooms",
        "required": ["name", "module", "code_presentation", "teacher_id", "created_at", "updated_at"],
        "properties": {
            "_id":               {"bsonType": "objectId"},
            "name":              {"bsonType": "string"},
            "module":            {"bsonType": "string", "description": "Ref courses.code_module"},
            "code_presentation": {"bsonType": "string"},
            "teacher_id":        {"bsonType": ["string", "int"]},
            "student_ids":       {"bsonType": "array", "items": {"bsonType": ["int", "string"]}},
            "description":       {"bsonType": ["string", "null"]},
            "status":            {"enum": ["active", "archived", "deleted"]},
            "created_at":        {"bsonType": ["date", "string"]},
            "updated_at":        {"bsonType": ["date", "string"]},
        },
    }
}

TIMETABLE_BLOCKS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "title": "timetable_blocks",
        "required": ["student_id", "current_week", "total_weeks", "created_at", "updated_at"],
        "properties": {
            "_id":          {"bsonType": "objectId"},
            "student_id":   {"bsonType": "int"},
            "current_week": {"bsonType": "int"},
            "total_weeks":  {"bsonType": "int"},
            "streak_days":  {"bsonType": "int"},
            "classes": {
                "bsonType": "array",
                "items": {
                    "bsonType": "object",
                    "properties": {
                        "code_module": {"bsonType": "string"},
                        "title":       {"bsonType": "string"},
                        "day":         {"bsonType": "string"},
                        "time_start":  {"bsonType": "string"},
                        "time_end":    {"bsonType": "string"},
                        "location":    {"bsonType": "string"},
                    },
                },
            },
            "assignments": {"bsonType": "array"},
            "exams":        {"bsonType": "array"},
            "created_at":   {"bsonType": ["date", "string"]},
            "updated_at":   {"bsonType": ["date", "string"]},
        },
    }
}

STUDY_PLANS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "title": "study_plans",
        "required": ["student_id", "created_at", "updated_at"],
        "properties": {
            "_id":              {"bsonType": "objectId"},
            "student_id":       {"bsonType": "int"},
            "sessions": {
                "bsonType": "array",
                "items": {
                    "bsonType": "object",
                    "properties": {
                        "subject":      {"bsonType": "string"},
                        "type":         {"enum": ["review", "practice", "assignment"]},
                        "duration":     {"bsonType": "int"},
                        "day":          {"bsonType": "string"},
                        "time":         {"bsonType": "string"},
                        "sm2_interval": {"bsonType": "int"},
                    },
                },
            },
            "student_approved": {"bsonType": "bool"},
            "created_at":       {"bsonType": ["date", "string"]},
            "updated_at":       {"bsonType": ["date", "string"]},
        },
    }
}

ASSIGNMENTS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "title": "assignments",
        "required": ["code_module", "due_date", "created_at", "updated_at"],
        "properties": {
            "id_assessment":    {"bsonType": "int"},
            "code_module":      {"bsonType": "string"},
            "type":             {"enum": ["TMA", "CMA", "Exam"]},
            "weight":           {"bsonType": ["double", "int"], "minimum": 0, "maximum": 100},
            "due_date":         {"bsonType": ["date", "int", "string"]},
            "allowed_formats":  {"bsonType": "array", "items": {"bsonType": "string"}},
            "max_file_size_mb": {"bsonType": "int"},
            "created_at":       {"bsonType": ["date", "string"]},
            "updated_at":       {"bsonType": ["date", "string"]},
        },
    }
}

SUBMISSIONS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "title": "submissions",
        "required": ["id_assessment", "student_id", "file_name", "file_url", "submitted_at", "submitted_day"],
        "properties": {
            "_id":           {"bsonType": ["objectId", "string"]},
            "id_assessment": {"bsonType": "int"},
            "student_id":    {"bsonType": "int"},
            "file_name":     {"bsonType": "string"},
            "file_url":      {"bsonType": "string"},
            "file_type":     {"bsonType": ["string", "null"]},
            "status":        {"enum": ["submitted", "graded", "late"]},
            "score":         {"bsonType": ["double", "int", "null"], "minimum": 0, "maximum": 100},
            "feedback":      {"bsonType": ["string", "null"]},
            "submitted_at":  {"bsonType": ["date", "string"]},
            "submitted_day": {"bsonType": "int"},
            "updated_at":    {"bsonType": ["date", "string", "null"]},
        },
    }
}

ASSIGNMENT_MILESTONES_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "title": "assignment_milestones",
        "required": ["student_id", "id_assessment", "module", "title", "created_at"],
        "properties": {
            "_id":          {"bsonType": "objectId"},
            "student_id":   {"bsonType": "int"},
            "id_assessment": {"bsonType": "int"},
            "module":       {"bsonType": "string"},
            "title":        {"bsonType": "string"},
            "milestones": {
                "bsonType": "array",
                "items": {
                    "bsonType": "object",
                    "properties": {
                        "id":             {"bsonType": "string"},
                        "title":          {"bsonType": "string"},
                        "status":         {"enum": ["done", "in_progress", "pending"]},
                        "due_offset_days": {"bsonType": "int"},
                    },
                },
            },
            "created_at": {"bsonType": ["date", "string"]},
            "updated_at": {"bsonType": ["date", "string", "null"]},
        },
    }
}

NOTIFICATIONS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "title": "notifications",
        "required": ["student_id", "type", "read", "payload", "created_at"],
        "properties": {
            "_id":        {"bsonType": "objectId"},
            "student_id": {"bsonType": ["int", "string"]},
            "recipient_id": {"bsonType": ["string", "int", "null"]},
            "type": {
                "enum": [
                    "general_notice", "warning", "deadline_warning",
                    "intervention", "general", "academic_warning",
                    "assignment", "broadcast",
                ]
            },
            "read": {"bsonType": "bool"},
            "payload": {
                "bsonType": "object",
                "required": ["title", "body"],
                "properties": {
                    "title": {"bsonType": "string"},
                    "body":  {"bsonType": "string"},
                },
            },
            "course_code":      {"bsonType": ["string", "null"]},
            "sender_role":      {"enum": ["instructor", "system", None]},
            "is_broadcast_log": {"bsonType": "bool"},
            "target_count":     {"bsonType": ["int", "null"]},
            "created_at":       {"bsonType": ["date", "string"]},
        },
    }
}

CHANNELS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "title": "channels",
        "required": ["course_code", "type", "name", "is_read_only", "allowed_post_roles", "status", "created_at"],
        "properties": {
            "_id":               {"bsonType": "objectId"},
            "course_code":       {"bsonType": "string"},
            "type":              {"enum": ["announcement", "discussion"]},
            "name":              {"bsonType": "string"},
            "is_read_only":      {"bsonType": "bool"},
            "allowed_post_roles": {
                "bsonType": "array",
                "items": {"enum": ["instructor", "class_rep", "student"]},
            },
            "status":     {"enum": ["active", "archived", "deleted"]},
            "created_at": {"bsonType": ["date", "string"]},
            "updated_at": {"bsonType": ["date", "string", "null"]},
        },
    }
}

MESSAGES_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "title": "messages",
        "required": ["channel_id", "course_code", "sender_id", "sender_role", "content", "created_at"],
        "properties": {
            "_id":         {"bsonType": "objectId"},
            "channel_id":  {"bsonType": ["objectId", "string"]},
            "course_code": {"bsonType": "string"},
            "sender_id":   {"bsonType": ["int", "string"]},
            "sender_role": {"enum": ["instructor", "student", "class_rep"]},
            "content":     {"bsonType": "string"},
            "created_at":  {"bsonType": ["date", "string"]},
            "parent_id":   {"bsonType": ["objectId", "string", "null"]},
            "reactions": {
                "bsonType": "array",
                "items": {
                    "bsonType": "object",
                    "properties": {
                        "emoji":   {"bsonType": "string"},
                        "user_id": {"bsonType": ["int", "string"]},
                    },
                },
            },
            "file_url":   {"bsonType": ["string", "null"]},
            "file_name":  {"bsonType": ["string", "null"]},
            "file_type":  {"bsonType": ["string", "null"]},
            "updated_at": {"bsonType": ["date", "string", "null"]},
        },
    }
}

KNOWLEDGE_STATES_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "title": "knowledge_states",
        "required": ["student_id", "code_module", "updated_at"],
        "properties": {
            "_id":           {"bsonType": "objectId"},
            "student_id":    {"bsonType": "int"},
            "code_module":   {"bsonType": "string"},
            "topic_mastery": {"bsonType": "object", "description": "Map topic_name -> mastery_score [0.0-1.0]"},
            "updated_at":    {"bsonType": ["date", "string"]},
        },
    }
}

RISK_HISTORY_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "title": "risk_history",
        "required": ["student_id", "risk_score", "risk_tier", "recorded_at"],
        "properties": {
            "_id":         {"bsonType": "objectId"},
            "student_id":  {"bsonType": "int"},
            "risk_score":  {"bsonType": ["double", "int"], "minimum": 0, "maximum": 1},
            "risk_tier":   {"bsonType": "int", "minimum": 1, "maximum": 4},
            "flags":       {"bsonType": "array", "items": {"bsonType": "string"}},
            "recorded_at": {"bsonType": ["date", "string"]},
        },
    }
}

AGENT_LOGS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "title": "agent_logs",
        "required": ["student_id", "agent_name", "duration_ms", "status", "created_at"],
        "properties": {
            "_id":           {"bsonType": "objectId"},
            "student_id":    {"bsonType": "int"},
            "agent_name":    {"bsonType": "string"},
            "payload_data":  {"bsonType": ["object", "null"]},
            "duration_ms":   {"bsonType": "int"},
            "status":        {"enum": ["SUCCESS", "FAILED"]},
            "retry_count":   {"bsonType": "int"},
            "error_message": {"bsonType": ["string", "null"]},
            "created_at":    {"bsonType": ["date", "string"]},
        },
    }
}

RESOURCES_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "title": "resources",
        "required": ["code_module", "title", "url", "created_at"],
        "properties": {
            "_id":         {"bsonType": "objectId"},
            "student_id":  {"bsonType": ["int", "null"]},
            "code_module": {"bsonType": "string"},
            "title":       {"bsonType": "string"},
            "type":        {"enum": ["pdf", "video", "quiz", "article", None]},
            "url":         {"bsonType": "string"},
            "tags":        {"bsonType": "array", "items": {"bsonType": "string"}},
            "rating":      {"bsonType": ["double", "int", "null"], "minimum": 0, "maximum": 5},
            "bookmarked":  {"bsonType": "bool"},
            "created_at":  {"bsonType": ["date", "string"]},
        },
    }
}

AUDIT_LOGS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "title": "audit_logs",
        "required": ["user_id", "action", "created_at"],
        "properties": {
            "_id":        {"bsonType": "objectId"},
            "user_id":    {"bsonType": ["int", "string"]},
            "action":     {"bsonType": "string"},
            "course_code": {"bsonType": ["string", "null"]},
            "metadata":   {"bsonType": "object"},
            "created_at": {"bsonType": ["date", "string"]},
        },
    }
}

# Map collection name -> schema
ALL_SCHEMAS = {
    "students":             STUDENTS_SCHEMA,
    "courses":              COURSES_SCHEMA,
    "classrooms":           CLASSROOMS_SCHEMA,
    "timetable_blocks":     TIMETABLE_BLOCKS_SCHEMA,
    "study_plans":          STUDY_PLANS_SCHEMA,
    "assignments":          ASSIGNMENTS_SCHEMA,
    "submissions":          SUBMISSIONS_SCHEMA,
    "assignment_milestones": ASSIGNMENT_MILESTONES_SCHEMA,
    "notifications":        NOTIFICATIONS_SCHEMA,
    "channels":             CHANNELS_SCHEMA,
    "messages":             MESSAGES_SCHEMA,
    "knowledge_states":     KNOWLEDGE_STATES_SCHEMA,
    "risk_history":         RISK_HISTORY_SCHEMA,
    "agent_logs":           AGENT_LOGS_SCHEMA,
    "resources":            RESOURCES_SCHEMA,
    "audit_logs":           AUDIT_LOGS_SCHEMA,
}
