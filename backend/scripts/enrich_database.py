"""
Fast Streamed Database Enrichment & Demo Seeding Script
======================================================
"""

import asyncio
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

IMD_BANDS = [
    "0-10%", "10-20%", "20-30%", "30-40%", "40-50%",
    "50-60%", "60-70%", "70-80%", "80-90%", "90-100%"
]

REGIONS = [
    "Hà Nội", "TP. Hồ Chí Minh", "Đà Nẵng", "Hải Phòng",
    "Cần Thơ", "Thái Nguyên", "Huế", "Nghệ An"
]

EDUCATIONS = [
    "A Level or Equivalent", "HE Qualification", "Lower Than A Level",
    "Post Graduate Qualification"
]

VIETNAMESE_NAMES = [
    "Nguyễn Văn An", "Trần Thị Mai", "Lê Hải Anh", "Phạm Quốc Bảo",
    "Hoàng Minh Đức", "Vũ Phương Linh", "Đặng Văn Khánh", "Bùi Thu Trang",
    "Đỗ Đức Thắng", "Hồ Hoàng Nam", "Ngô Quang Huy", "Dương Gia Bảo",
    "Lý Quỳnh Nga", "Phan Tuấn Kiệt", "Trịnh Bảo Ngọc", "Đinh Hữu Phước",
    "Võ Thành Đạt", "Lâm Quốc Cường", "Mai Hồng Nhung", "Trương Thảo My",
    "Lê Hoàng Long", "Nguyễn Đình Trọng", "Trần Khánh Huyền", "Phạm Tuấn Anh",
    "Hoàng Bảo Trâm", "Vũ Minh Quân", "Đặng Thùy Dương", "Bùi Thế Anh",
    "Đỗ Thảo Vy", "Hồ Minh Quân", "Ngô Bích Ngọc", "Dương Nhật Minh",
    "Lý Tiến Dũng", "Phan Lan Anh", "Trịnh Hoàng Yến", "Đinh Quốc Việt",
    "Võ Thị Cẩm Nhung", "Lâm Hoàng Phúc", "Mai Phương Thảo", "Trương Minh Triết"
]

def generate_risk_trajectory(tier: int, seed_val: int):
    rng = random.Random(seed_val)
    risk_weeks = []
    tier_weeks = []
    if tier == 1:
        base = rng.uniform(0.08, 0.22)
        for w in range(1, 41):
            val = max(0.04, min(0.32, base + rng.uniform(-0.03, 0.03) + (w * 0.001)))
            risk_weeks.append(round(val, 3))
            tier_weeks.append(1)
    elif tier == 2:
        base = rng.uniform(0.38, 0.52)
        for w in range(1, 41):
            val = max(0.34, min(0.62, base + rng.uniform(-0.04, 0.04) + (w * 0.002)))
            risk_weeks.append(round(val, 3))
            tier_weeks.append(2 if val < 0.65 else 3)
    else:
        base = rng.uniform(0.55, 0.72)
        for w in range(1, 41):
            val = max(0.45, min(0.95, base + rng.uniform(-0.04, 0.06) + (w - 1) * 0.007))
            risk_weeks.append(round(val, 3))
            tier_weeks.append(3 if val >= 0.65 else 2)
    return risk_weeks, tier_weeks

def generate_assessments(tier: int, seed_val: int):
    rng = random.Random(seed_val)
    if tier == 1:
        s1 = rng.randint(82, 98)
        s2 = rng.randint(80, 96)
        s3 = rng.randint(85, 99)
        s4 = rng.randint(80, 95)
        d1, d2, d3, d4 = 25, 53, 82, 140
    elif tier == 2:
        s1 = rng.randint(62, 78)
        s2 = rng.randint(58, 72)
        s3 = rng.randint(60, 75)
        s4 = rng.randint(55, 70)
        d1, d2, d3, d4 = 28, 57, 85, 140
    else:
        s1 = rng.randint(35, 52)
        s2 = rng.randint(25, 48) if rng.random() > 0.3 else None
        s3 = rng.randint(30, 50)
        s4 = rng.randint(20, 45) if rng.random() > 0.4 else None
        d1 = 32
        d2 = 60 if s2 is not None else None
        d3 = 88
        d4 = 140 if s4 is not None else None

    return [
        {"id_assessment": seed_val * 10 + 1, "type": "TMA", "due_date": 28, "weight": 20, "score": s1, "submitted_date": d1, "is_banked": False},
        {"id_assessment": seed_val * 10 + 2, "type": "TMA", "due_date": 56, "weight": 20, "score": s2, "submitted_date": d2, "is_banked": False},
        {"id_assessment": seed_val * 10 + 3, "type": "CMA", "due_date": 84, "weight": 20, "score": s3, "submitted_date": d3, "is_banked": False},
        {"id_assessment": seed_val * 10 + 4, "type": "Exam", "due_date": 140, "weight": 40, "score": s4, "submitted_date": d4, "is_banked": False}
    ]

def generate_vle_clicks(tier: int, seed_val: int):
    rng = random.Random(seed_val)
    if tier == 1:
        return [rng.randint(280, 500) for _ in range(40)]
    elif tier == 2:
        return [rng.randint(120, 260) for _ in range(40)]
    else:
        return [int(rng.randint(40, 110) * max(0.15, 1.0 - w * 0.025)) for w in range(40)]

async def main():
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB", "education-system")
    print(f"[*] Connecting to MongoDB {db_name}...", flush=True)
    client = AsyncIOMotorClient(uri)
    db = client[db_name]

    now_iso = datetime.now(timezone.utc).isoformat()

    # 1. Update Students in batches
    print("[*] Streaming and enriching students...", flush=True)
    cursor = db["students"].find({}, {"_id": 1, "student_id": 1, "name": 1, "full_name": 1, "enrollments": 1})
    ops = []
    count = 0

    async for s in cursor:
        sid = s.get("student_id") or (10000 + count)
        mod_val = (sid + count) % 20
        if mod_val < 13:
            tier = 1
            score = round(0.06 + (sid % 25) * 0.01, 2)
            flags = []
            final_res = "Distinction" if score < 0.12 else "Pass"
        elif mod_val < 17:
            tier = 2
            score = round(0.38 + (sid % 24) * 0.01, 2)
            flags = ["moderate_vle_activity", "upcoming_milestone"]
            final_res = "Pass"
        else:
            tier = 3
            score = round(0.68 + (sid % 26) * 0.01, 2)
            flags = ["low_vle_engagement", "assessment_shock", "missed_submission"]
            final_res = "Fail" if score > 0.85 else "Withdrawn" if score > 0.90 else "Pass"

        age_num = 20 + ((sid + count) % 5)
        imd_band = IMD_BANDS[(sid + count) % len(IMD_BANDS)]
        region = REGIONS[(sid + count) % len(REGIONS)]
        education = EDUCATIONS[(sid + count) % len(EDUCATIONS)]
        prev_attempts = 1 if tier == 3 and (sid % 3 == 0) else 0
        credits = 60 + ((sid % 4) * 30)

        vn_name = s.get("full_name") or s.get("name")
        if not vn_name or vn_name.startswith("Student #"):
            vn_name = VIETNAMESE_NAMES[(sid + count) % len(VIETNAMESE_NAMES)]

        updated_enrollments = []
        for e in s.get("enrollments", []):
            c_mod = e.get("code_module", "")
            c_pres = e.get("code_presentation", "")
            assessments = generate_assessments(tier, sid + len(c_mod))
            weekly_clicks = generate_vle_clicks(tier, sid + len(c_pres))
            total_clicks = sum(weekly_clicks)
            scored = [a for a in assessments if a.get("score") is not None]
            tot_w = sum(a.get("weight", 1) for a in scored)
            w_score = round(sum(a["score"] * a.get("weight", 1) for a in scored) / tot_w, 1) if tot_w > 0 else 80.0

            updated_enrollments.append({
                **e,
                "final_result": final_res,
                "avg_score": w_score,
                "gpa": round(w_score / 10.0, 2),
                "assessments": assessments,
                "vle_summary": {
                    "last_active_day": 95 if tier == 1 else 80 if tier == 2 else 42,
                    "total_clicks": total_clicks,
                    "by_activity_type": {
                        "resource": int(total_clicks * 0.35),
                        "oucontent": int(total_clicks * 0.30),
                        "forumng": int(total_clicks * 0.15),
                        "quiz": int(total_clicks * 0.10),
                        "homepage": int(total_clicks * 0.10),
                    },
                    "weekly_clicks": weekly_clicks,
                }
            })

        risk_by_week, tier_by_week = generate_risk_trajectory(tier, sid)

        update_fields = {
            "name": vn_name,
            "full_name": vn_name,
            "demographics.name": vn_name,
            "demographics.age_band": str(age_num),
            "demographics.age": age_num,
            "demographics.imd_band": imd_band,
            "demographics.region": region,
            "demographics.highest_education": education,
            "demographics.num_prev_attempts": prev_attempts,
            "demographics.studied_credits": credits,
            "risk": {
                "tier": tier,
                "score": score,
                "flags": flags,
                "computed_at": now_iso,
            },
            "risk_by_week": risk_by_week,
            "tier_by_week": tier_by_week,
            "enrollments": updated_enrollments,
            "avg_score": updated_enrollments[0]["avg_score"] if updated_enrollments else 80.0,
            "updated_at": now_iso,
        }

        ops.append(UpdateOne({"_id": s["_id"]}, {"$set": update_fields}))
        count += 1

        if len(ops) >= 500:
            await db["students"].bulk_write(ops, ordered=False)
            print(f"    - Processed {count} students...", flush=True)
            ops = []

    if ops:
        await db["students"].bulk_write(ops, ordered=False)
        print(f"    - Processed {count} students (Final).", flush=True)

    print(f"[+] Successfully enriched {count} students with Vietnamese names!", flush=True)

    # 2. Extract All Active Courses & Enrollments
    print("[*] Detecting all courses from database and enrollments...", flush=True)
    enrolled_courses = await db["students"].aggregate([
        {"$unwind": "$enrollments"},
        {"$group": {"_id": {
            "module": "$enrollments.code_module",
            "presentation": "$enrollments.code_presentation"
        }}}
    ]).to_list(None)

    course_keys = set()
    for ec in enrolled_courses:
        m = ec["_id"].get("module")
        p = ec["_id"].get("presentation")
        if m and p:
            course_keys.add((m, p))

    db_courses = await db["courses"].find({}).to_list(None)
    course_meta = {}
    for c in db_courses:
        m = c.get("code_module") or c.get("module")
        p = c.get("code_presentation") or c.get("presentation")
        if m and p:
            course_keys.add((m, p))
            course_meta[(m, p)] = c.get("title") or c.get("name") or m

    # Ensure all courses are registered in db.courses
    for (m, p) in course_keys:
        title = course_meta.get((m, p)) or f"Course {m} ({p})"
        await db["courses"].update_one(
            {"$or": [{"code_module": m, "code_presentation": p}, {"module": m, "presentation": p}]},
            {"$set": {
                "code_module": m,
                "code_presentation": p,
                "module": m,
                "presentation": p,
                "title": title,
                "name": title,
                "updated_at": now_iso
            }},
            upsert=True
        )

    print(f"[*] Found {len(course_keys)} unique course offerings. Seeding channels, messages, study groups & notifications...", flush=True)

    # Clean old channels, messages, study groups, notifications to ensure clean state
    await db["channels"].delete_many({})
    await db["messages"].delete_many({})
    await db["study_groups"].delete_many({})
    await db["notifications"].delete_many({})

    all_notifications = []
    all_study_groups = []

    for (m, p) in course_keys:
        course_code = f"{m} {p}"
        title = course_meta.get((m, p)) or f"Course {m}"

        # Fetch enrolled students for this course
        c_students = await db["students"].find(
            {"enrollments": {"$elemMatch": {"code_module": m, "code_presentation": p}}},
            {"student_id": 1, "name": 1, "full_name": 1, "risk.tier": 1}
        ).limit(60).to_list(None)

        if not c_students:
            c_students = await db["students"].find({}, {"student_id": 1, "name": 1, "full_name": 1, "risk.tier": 1}).limit(30).to_list(None)

        t3_list = [s for s in c_students if s.get("risk", {}).get("tier") == 3]
        t2_list = [s for s in c_students if s.get("risk", {}).get("tier") == 2]
        t1_list = [s for s in c_students if s.get("risk", {}).get("tier") == 1]

        # 1. Announcement Channel
        ann_res = await db["channels"].insert_one({
            "course_code": course_code,
            "type": "announcement",
            "name": f"Announcements — {title}",
            "is_read_only": True,
            "allowed_post_roles": ["instructor", "class_rep"],
            "status": "active",
            "created_at": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),
        })
        ann_id = str(ann_res.inserted_id)

        # 2. Discussion Channel
        disc_res = await db["channels"].insert_one({
            "course_code": course_code,
            "type": "discussion",
            "name": f"General Discussions — {title}",
            "is_read_only": False,
            "allowed_post_roles": ["student", "instructor", "class_rep"],
            "status": "active",
            "created_at": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),
        })
        disc_id = str(disc_res.inserted_id)

        # Student representatives for chat simulation
        st1 = t1_list[0] if t1_list else c_students[0]
        st2 = t2_list[0] if t2_list else (c_students[1] if len(c_students) > 1 else c_students[0])
        st3 = t3_list[0] if t3_list else (c_students[2] if len(c_students) > 2 else c_students[0])
        st4 = c_students[3] if len(c_students) > 3 else c_students[0]

        st1_name = st1.get("full_name") or st1.get("name", "Nguyễn Văn An")
        st2_name = st2.get("full_name") or st2.get("name", "Đặng Văn Khánh")
        st3_name = st3.get("full_name") or st3.get("name", "Trần Thị Mai")
        st4_name = st4.get("full_name") or st4.get("name", "Lê Văn Hùng")

        # Seed Messages for Announcements & Discussions
        course_messages = [
            # Announcements
            {
                "channel_id": ann_id,
                "course_code": course_code,
                "sender_id": "instructor_1",
                "sender_name": "Dr. Nguyen Minh Tuan (Instructor)",
                "sender_role": "instructor",
                "content": f"📢 **Welcome all students to {title} ({course_code})!**\n\nThe course syllabus, lecture slides, and assessment schedules have been uploaded to the portal. Please monitor upcoming TMA milestones and scheduled quizzes closely.",
                "created_at": (datetime.now(timezone.utc) - timedelta(days=25)).isoformat(),
                "parent_id": None,
                "reactions": [{"emoji": "👍", "count": 18}, {"emoji": "❤️", "count": 12}],
            },
            {
                "channel_id": ann_id,
                "course_code": course_code,
                "sender_id": "instructor_1",
                "sender_name": "Dr. Nguyen Minh Tuan (Instructor)",
                "sender_role": "instructor",
                "content": "⏰ **ASSESSMENT DEADLINE REMINDER: TMA-01**\n\nThe submission deadline for TMA-01 is this Sunday at 23:59. Please ensure your PDF submissions comply with the formatting guidelines. Late submissions will not be accepted!",
                "created_at": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
                "parent_id": None,
                "reactions": [{"emoji": "⚡", "count": 8}, {"emoji": "🔥", "count": 5}],
            },
            {
                "channel_id": ann_id,
                "course_code": course_code,
                "sender_id": "instructor_1",
                "sender_name": "Dr. Nguyen Minh Tuan (Instructor)",
                "sender_role": "instructor",
                "content": "📚 **MIDTERM REVIEW SESSION & Q&A GUIDANCE**\n\nAn online tutorial and Q&A review session before the midterm examination will take place this Friday at 19:30. Please prepare your questions in advance.",
                "created_at": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat(),
                "parent_id": None,
                "reactions": [{"emoji": "🙌", "count": 15}],
            },
            # Discussions
            {
                "channel_id": disc_id,
                "course_code": course_code,
                "sender_id": str(st1["student_id"]),
                "sender_name": st1_name,
                "sender_role": "student",
                "content": f"Dear Instructor and classmates, for Question 3 in TMA-01 for {m}, should we plot a distribution chart or is numeric justification sufficient?",
                "created_at": (datetime.now(timezone.utc) - timedelta(days=8, hours=4)).isoformat(),
                "parent_id": None,
                "reactions": [{"emoji": "💡", "count": 4}],
            },
            {
                "channel_id": disc_id,
                "course_code": course_code,
                "sender_id": "instructor_1",
                "sender_name": "Dr. Nguyen Minh Tuan (Instructor)",
                "sender_role": "instructor",
                "content": f"@{st1_name} Including visual distributions (e.g. histograms or boxplots) alongside your numerical reasoning is strongly recommended and will earn higher marks!",
                "created_at": (datetime.now(timezone.utc) - timedelta(days=8, hours=2)).isoformat(),
                "parent_id": None,
                "reactions": [{"emoji": "👍", "count": 6}, {"emoji": "❤️", "count": 5}],
            },
            {
                "channel_id": disc_id,
                "course_code": course_code,
                "sender_id": str(st2["student_id"]),
                "sender_name": st2_name,
                "sender_role": "student",
                "content": "I implemented the variance calculation in Python and verified the expected results. Thank you for the guidance, Professor!",
                "created_at": (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),
                "parent_id": None,
                "reactions": [{"emoji": "🎉", "count": 3}],
            },
            {
                "channel_id": disc_id,
                "course_code": course_code,
                "sender_id": str(st3["student_id"]),
                "sender_name": st3_name,
                "sender_role": "student",
                "content": "Team members: let's meet on Google Meet tonight at 20:00 to review our assignment draft together!",
                "created_at": (datetime.now(timezone.utc) - timedelta(days=4)).isoformat(),
                "parent_id": None,
                "reactions": [{"emoji": "👌", "count": 5}],
            },
            {
                "channel_id": disc_id,
                "course_code": course_code,
                "sender_id": "ta_assistant",
                "sender_name": "Le Hoang Nam (Teaching Assistant)",
                "sender_role": "instructor",
                "content": f"Hello everyone, summary slides for {m} Chapter 3 have been published on the portal. Please download them for exam review.",
                "created_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
                "parent_id": None,
                "reactions": [{"emoji": "🙏", "count": 11}],
            }
        ]

        # 3. Direct Message Channels (Teacher <-> Students)
        dm_students = [st3, st2]
        for dm_st in dm_students:
            sid_str = str(dm_st["student_id"])
            s_name = dm_st.get("full_name") or dm_st.get("name") or f"Student #{sid_str}"
            members_key = f"teacher_admin|{sid_str}"
            
            existing_dm = await db["channels"].find_one({"type": "private_message", "members_key": members_key})
            if existing_dm:
                dm_chan_id = str(existing_dm["_id"])
            else:
                dm_chan_res = await db["channels"].insert_one({
                    "course_code": course_code,
                    "type": "private_message",
                    "name": f"{s_name} (#{sid_str})",
                    "members": ["teacher_admin", sid_str],
                    "members_key": members_key,
                    "is_read_only": False,
                    "allowed_post_roles": ["instructor", "student"],
                    "status": "active",
                    "created_at": (datetime.now(timezone.utc) - timedelta(days=6)).isoformat(),
                })
                dm_chan_id = str(dm_chan_res.inserted_id)

            course_messages.extend([
                {
                    "channel_id": dm_chan_id,
                    "course_code": course_code,
                    "sender_id": "teacher_admin",
                    "sender_name": "Dr. Nguyen Minh Tuan (Instructor)",
                    "sender_role": "instructor",
                    "content": f"Hi {s_name.split()[-1]}, I noticed your recent quiz submission in {m} could be improved. How is your preparation for TMA-01 going?",
                    "created_at": (datetime.now(timezone.utc) - timedelta(days=5, hours=3)).isoformat(),
                    "parent_id": None,
                },
                {
                    "channel_id": dm_chan_id,
                    "course_code": course_code,
                    "sender_id": sid_str,
                    "sender_name": s_name,
                    "sender_role": "student",
                    "content": "Hello Professor! Thank you for reaching out. I had difficulty with some statistical concepts in Chapter 2, but I am following the practice exercises now.",
                    "created_at": (datetime.now(timezone.utc) - timedelta(days=5, hours=1)).isoformat(),
                    "parent_id": None,
                },
                {
                    "channel_id": dm_chan_id,
                    "course_code": course_code,
                    "sender_id": "teacher_admin",
                    "sender_name": "Dr. Nguyen Minh Tuan (Instructor)",
                    "sender_role": "instructor",
                    "content": "Feel free to book a 15-minute 1-on-1 tutoring slot during my office hours this Thursday at 14:00. Keep up the good effort!",
                    "created_at": (datetime.now(timezone.utc) - timedelta(days=4, hours=20)).isoformat(),
                    "parent_id": None,
                },
                {
                    "channel_id": dm_chan_id,
                    "course_code": course_code,
                    "sender_id": sid_str,
                    "sender_name": s_name,
                    "sender_role": "student",
                    "content": "Thank you so much Professor! I will register for the slot and prepare my questions.",
                    "created_at": (datetime.now(timezone.utc) - timedelta(days=4, hours=18)).isoformat(),
                    "parent_id": None,
                }
            ])

        # 4. Private Group Chat
        group_members = ["teacher_admin"] + [str(s["student_id"]) for s in [st1, st2, st3, st4]]
        grp_chan_res = await db["channels"].insert_one({
            "course_code": course_code,
            "type": "private_group",
            "name": f"Academic Support & Review Group — {m} ({p})",
            "members": group_members,
            "is_read_only": False,
            "allowed_post_roles": ["instructor", "student"],
            "status": "active",
            "created_at": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
        })
        grp_chan_id = str(grp_chan_res.inserted_id)

        course_messages.extend([
            {
                "channel_id": grp_chan_id,
                "course_code": course_code,
                "sender_id": "teacher_admin",
                "sender_name": "Dr. Nguyen Minh Tuan (Instructor)",
                "sender_role": "instructor",
                "content": f"Welcome to the Academic Support Group for {m}. You can collaborate on weekly assignments and share practice materials here.",
                "created_at": (datetime.now(timezone.utc) - timedelta(days=9)).isoformat(),
                "parent_id": None,
            },
            {
                "channel_id": grp_chan_id,
                "course_code": course_code,
                "sender_id": str(st1["student_id"]),
                "sender_name": st1.get("name", "Nguyễn Văn An"),
                "sender_role": "student",
                "content": "Hello everyone! I created a shared Google Doc for our group problem set.",
                "created_at": (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),
                "parent_id": None,
            },
            {
                "channel_id": grp_chan_id,
                "course_code": course_code,
                "sender_id": str(st3["student_id"]),
                "sender_name": st3.get("name", "Trần Thị Mai"),
                "sender_role": "student",
                "content": "Great, I will add my solutions for questions 1 and 2 by tonight.",
                "created_at": (datetime.now(timezone.utc) - timedelta(days=6)).isoformat(),
                "parent_id": None,
            }
        ])

        await db["messages"].insert_many(course_messages)

        # 5. Study Groups Collection
        all_study_groups.extend([
            {
                "group_code": f"GRP-{m}-01",
                "name": f"Team 1 — {title} Core Review",
                "description": f"Peer learning group for statistical modeling, TMA-01 and TMA-02 preparation for {m}.",
                "created_by": str(st1["student_id"]),
                "leader_id": str(st1["student_id"]),
                "leader_name": st1.get("name", "Nguyễn Văn An"),
                "course_code": course_code,
                "module": m,
                "presentation": p,
                "members": [str(st1["student_id"]), str(st2["student_id"]), str(st3["student_id"])],
                "messages": [
                    {"id": "msg_01", "sender_id": str(st1["student_id"]), "sender_name": st1.get("name", "Nguyễn Văn An"), "content": "Hi everyone! Let's consolidate our regression analysis findings tonight at 20:00.", "created_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(), "type": "text"},
                    {"id": "msg_02", "sender_id": str(st2["student_id"]), "sender_name": st2.get("name", "Đặng Văn Khánh"), "content": "I have prepared the Python Jupyter notebook and plotted the correlation matrix.", "created_at": (datetime.now(timezone.utc) - timedelta(days=5, minutes=-20)).isoformat(), "type": "text"},
                    {"id": "msg_03", "sender_id": str(st3["student_id"]), "sender_name": st3.get("name", "Trần Thị Mai"), "content": "Awesome! I will take care of interpreting the p-value significance and model summary.", "created_at": (datetime.now(timezone.utc) - timedelta(days=4)).isoformat(), "type": "text"},
                ],
                "resources": [{"id": "res_01", "title": f"Summary Slides - {m}.pdf", "url": f"https://example.com/slides-{m}.pdf", "shared_by": st1.get("name", "Nguyễn Văn An"), "created_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()}],
                "created_at": (datetime.now(timezone.utc) - timedelta(days=15)).isoformat(),
                "last_active_at": datetime.now(timezone.utc).isoformat(),
                "member_count": 3
            },
            {
                "group_code": f"GRP-{m}-02",
                "name": f"Team 2 — Presentation & Practical Lab ({m})",
                "description": f"Collaborative study group for team presentation and final practical report for {m}.",
                "created_by": str(st2["student_id"]),
                "leader_id": str(st2["student_id"]),
                "leader_name": st2.get("name", "Đặng Văn Khánh"),
                "course_code": course_code,
                "module": m,
                "presentation": p,
                "members": [str(st2["student_id"]), str(st3["student_id"]), str(st4["student_id"])],
                "messages": [
                    {"id": "msg_11", "sender_id": str(st2["student_id"]), "sender_name": st2.get("name", "Đặng Văn Khánh"), "content": "Has everyone finalized their presentation topic sections?", "created_at": (datetime.now(timezone.utc) - timedelta(days=6)).isoformat(), "type": "text"},
                    {"id": "msg_12", "sender_id": str(st4["student_id"]), "sender_name": st4.get("name", "Lê Văn Hùng"), "content": "Our group confirmed the topic 'Applied Machine Learning Workflow'.", "created_at": (datetime.now(timezone.utc) - timedelta(days=6, minutes=-15)).isoformat(), "type": "text"},
                ],
                "resources": [],
                "created_at": (datetime.now(timezone.utc) - timedelta(days=12)).isoformat(),
                "last_active_at": datetime.now(timezone.utc).isoformat(),
                "member_count": 3
            }
        ])

        # 6. Notifications for this course
        # Broadcast Logs (visible in Teacher System Inbox for this course)
        all_notifications.extend([
            {
                "student_id": 0,
                "recipient_id": "teacher_admin",
                "type": "academic_warning",
                "read": True,
                "sender_role": "instructor",
                "senderRole": "Instructor",
                "receiverRole": "Student",
                "course_code": course_code,
                "module": m,
                "presentation": p,
                "is_broadcast_log": True,
                "target_count": len(t3_list) if t3_list else 12,
                "payload": {
                    "title": f"[ACADEMIC WARNING] Performance Support Guidance [TIER 3]",
                    "body": f"Broadcast academic support and warning notices to {len(t3_list) if t3_list else 12} high-risk students in {title} ({course_code})."
                },
                "title": f"[ACADEMIC WARNING] Performance Support Guidance [TIER 3]",
                "content": f"Broadcast academic support and warning notices to {len(t3_list) if t3_list else 12} high-risk students in {title} ({course_code}).",
                "created_at": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
                "createdAt": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
            },
            {
                "student_id": 0,
                "recipient_id": "teacher_admin",
                "type": "study_reminder",
                "read": True,
                "sender_role": "instructor",
                "senderRole": "Instructor",
                "receiverRole": "Student",
                "course_code": course_code,
                "module": m,
                "presentation": p,
                "is_broadcast_log": True,
                "target_count": len(t2_list) if t2_list else 25,
                "payload": {
                    "title": f"[PROGRESS REMINDER] Assessment Deadlines & Core Review [TIER 2]",
                    "body": f"Sent progress reminder and study guidelines to {len(t2_list) if t2_list else 25} moderate-risk students in {title}."
                },
                "title": f"[PROGRESS REMINDER] Assessment Deadlines & Core Review [TIER 2]",
                "content": f"Sent progress reminder and study guidelines to {len(t2_list) if t2_list else 25} moderate-risk students in {title}.",
                "created_at": (datetime.now(timezone.utc) - timedelta(days=4)).isoformat(),
                "createdAt": (datetime.now(timezone.utc) - timedelta(days=4)).isoformat(),
            },
            {
                "student_id": 0,
                "recipient_id": "teacher_admin",
                "type": "exam_schedule",
                "read": True,
                "sender_role": "instructor",
                "senderRole": "Instructor",
                "receiverRole": "Student",
                "course_code": course_code,
                "module": m,
                "presentation": p,
                "is_broadcast_log": True,
                "target_count": len(c_students),
                "payload": {
                    "title": f"Midterm Examination Schedule Announcement",
                    "body": f"Broadcast midterm examination schedule and exam hall regulations to {len(c_students)} enrolled students in {title} ({course_code})."
                },
                "title": f"Midterm Examination Schedule Announcement",
                "content": f"Broadcast midterm examination schedule and exam hall regulations to {len(c_students)} enrolled students in {title} ({course_code}).",
                "created_at": (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),
                "createdAt": (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),
            },
            {
                "student_id": 0,
                "recipient_id": "teacher_admin",
                "type": "makeup_class",
                "read": True,
                "sender_role": "instructor",
                "senderRole": "Instructor",
                "receiverRole": "Student",
                "course_code": course_code,
                "module": m,
                "presentation": p,
                "is_broadcast_log": True,
                "target_count": len(c_students),
                "payload": {
                    "title": f"[TUTORIAL] Extra Problem Solving Workshop",
                    "body": f"Notified students about the weekend problem-solving workshop for {title} on Google Meet."
                },
                "title": f"[TUTORIAL] Extra Problem Solving Workshop",
                "content": f"Notified students about the weekend problem-solving workshop for {title} on Google Meet.",
                "created_at": (datetime.now(timezone.utc) - timedelta(days=12)).isoformat(),
                "createdAt": (datetime.now(timezone.utc) - timedelta(days=12)).isoformat(),
            }
        ])

        # Individual notifications to actual students
        for s in t3_list:
            all_notifications.append({
                "student_id": s["student_id"],
                "type": "academic_warning",
                "read": False,
                "sender_role": "instructor",
                "course_code": course_code,
                "module": m,
                "presentation": p,
                "payload": {
                    "title": f"[ACADEMIC WARNING] Support Guidance for {m}",
                    "body": f"Our academic tracking system indicates that your progress in {title} ({course_code}) needs improvement. Please contact your instructor this week for academic assistance."
                },
                "created_at": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
                "is_broadcast_log": False,
            })

        for s in t2_list:
            all_notifications.append({
                "student_id": s["student_id"],
                "type": "study_reminder",
                "read": False,
                "sender_role": "instructor",
                "course_code": course_code,
                "module": m,
                "presentation": p,
                "payload": {
                    "title": f"[STUDY REMINDER] Assessment Deadlines for {m}",
                    "body": f"The TMA-01 assessment deadline for {title} is approaching. Please review Chapter 2 & 3 and submit before the due date."
                },
                "created_at": (datetime.now(timezone.utc) - timedelta(days=4)).isoformat(),
                "is_broadcast_log": False,
            })

        for s in c_students[:15]:
            all_notifications.append({
                "student_id": s["student_id"],
                "type": "exam_schedule",
                "read": True,
                "sender_role": "instructor",
                "course_code": course_code,
                "module": m,
                "presentation": p,
                "payload": {
                    "title": f"Midterm Examination Schedule for {m}",
                    "body": f"The midterm examination for {title} will be held at 08:00 AM in Hall A201. Please arrive 15 minutes early."
                },
                "created_at": (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),
                "is_broadcast_log": False,
            })

    if all_study_groups:
        await db["study_groups"].insert_many(all_study_groups)
    if all_notifications:
        await db["notifications"].insert_many(all_notifications)

    print(f"[+] Successfully seeded {len(all_study_groups)} study groups across all courses!", flush=True)
    print(f"[+] Successfully seeded {len(all_notifications)} notifications across all courses!", flush=True)
    print("\n✨ ALL SEEDING & ENRICHMENT COMPLETED SUCCESSFULLY! ✨\n", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
