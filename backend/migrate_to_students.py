import asyncio, os, sys
from datetime import datetime, timezone
sys.stdout.reconfigure(encoding='utf-8')
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import bcrypt

load_dotenv()

async def main():
    uri = os.getenv("MONGODB_URI", "")
    db_name = os.getenv("MONGODB_DB", "education-system")
    client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=10000)
    db = client[db_name]

    print("=== Bắt đầu migration ===")
    
    # Hash password "123456"
    pwd_bytes = "123456".encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_pwd = bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

    students_map = {} # id_student -> student_doc

    def get_or_create_student(sid, name, email=None, gender="M", region="Unknown", highest_education="Unknown", imd_band="Unknown", age_band="Unknown", disability=False, num_prev_attempts=0, studied_credits=0):
        if sid not in students_map:
            short_name = " ".join(name.split()[-2:]) if name else ""
            students_map[sid] = {
                "student_id": sid,
                "auth0_id": f"auth0|{sid}",
                "full_name": name,
                "short_name": short_name,
                "email": email or f"student{sid}@edu.vn",
                "password_hash": hashed_pwd,
                "is_active": True,
                "avatar_url": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "demographics": {
                    "gender": gender,
                    "age_band": age_band,
                    "region": region,
                    "highest_education": highest_education,
                    "imd_band": imd_band,
                    "disability": disability,
                    "num_prev_attempts": num_prev_attempts,
                    "studied_credits": studied_credits,
                },
                "enrollments": [],
                "risk": {
                    "tier": 1,
                    "score": 0.1,
                    "flags": [],
                    "computed_at": datetime.now(timezone.utc).isoformat()
                },
                "prerequisite_gaps": []
            }
        return students_map[sid]

    # 1. Load processed_students
    print("Loading processed_students...")
    async for pdoc in db["processed_students"].find({}):
        sid = pdoc.get("id_student")
        if not sid: continue
        
        name = pdoc.get("name", f"Student {sid}")
        student = get_or_create_student(
            sid, name, 
            gender=pdoc.get("gender", "M"),
            region=pdoc.get("region", "Unknown"),
            highest_education=pdoc.get("highest_education", "Unknown"),
            imd_band=pdoc.get("imd_band", "Unknown"),
            age_band=pdoc.get("age_band", "Unknown"),
            disability=pdoc.get("disability", False),
            num_prev_attempts=pdoc.get("num_of_prev_attempts", 0),
            studied_credits=pdoc.get("studied_credits", 0)
        )
        
        # Add enrollment
        enrollment = {
            "code_module": pdoc.get("code_module", ""),
            "code_presentation": pdoc.get("code_presentation", ""),
            "title": pdoc.get("code_module", ""),
            "module_length": pdoc.get("module_presentation_length", 30),
            "registration_date": pdoc.get("date_registration", 0),
            "unregistration_date": pdoc.get("date_unregistration"),
            "final_result": pdoc.get("final_result"),
            "assessments": pdoc.get("assessments", []),
            "vle_summary": {
                "total_clicks": sum(pdoc.get("weekly_clicks", [])),
                "last_active_day": 0,
                "by_activity_type": {},
                "weekly_clicks": pdoc.get("weekly_clicks", [])
            }
        }
        student["enrollments"].append(enrollment)
        
        # Update risk if possible
        tier_by_week = pdoc.get("tier_by_week", [])
        risk_by_week = pdoc.get("risk_by_week", [])
        if tier_by_week:
            student["risk"]["tier"] = int(tier_by_week[-1])
        if risk_by_week:
            student["risk"]["score"] = float(risk_by_week[-1])

    # 2. Load custom_students
    print("Loading custom_students...")
    async for cdoc in db["custom_students"].find({}):
        sid = cdoc.get("id_student") or cdoc.get("student_id")
        if not sid: continue
        
        name = cdoc.get("name", f"Student {sid}")
        email = cdoc.get("email", f"student{sid}@edu.vn")
        student = get_or_create_student(
            sid, name, email,
            gender=cdoc.get("gender", "M"),
            region=cdoc.get("region", "Unknown"),
            highest_education=cdoc.get("highest_education", "Unknown"),
            imd_band=cdoc.get("imd_band", "Unknown"),
            age_band=cdoc.get("age_band", "Unknown"),
            disability=cdoc.get("disability", False),
            num_prev_attempts=cdoc.get("num_of_prev_attempts", 0),
            studied_credits=cdoc.get("studied_credits", 0)
        )
        
        enrollment = {
            "code_module": cdoc.get("code_module", ""),
            "code_presentation": cdoc.get("code_presentation", ""),
            "title": cdoc.get("code_module", ""),
            "module_length": 30,
            "registration_date": cdoc.get("date_registration", 0),
            "unregistration_date": None,
            "final_result": cdoc.get("final_result"),
            "assessments": [],
            "vle_summary": {
                "total_clicks": 0,
                "last_active_day": 0,
                "by_activity_type": {},
                "weekly_clicks": []
            }
        }
        # Avoid duplicate enrollments
        existing_codes = [(e["code_module"], e["code_presentation"]) for e in student["enrollments"]]
        if (enrollment["code_module"], enrollment["code_presentation"]) not in existing_codes:
            student["enrollments"].append(enrollment)

    print(f"Tổng số sinh viên cần lưu: {len(students_map)}")

    # 3. Ghi vào collection students
    print("Đang lưu vào DB (bảng students)...")
    operations = []
    from pymongo import UpdateOne
    for sid, sdoc in students_map.items():
        operations.append(UpdateOne(
            {"student_id": sid},
            {"$set": sdoc},
            upsert=True
        ))
    
    if operations:
        # Batch insert/update in chunks
        chunk_size = 1000
        for i in range(0, len(operations), chunk_size):
            chunk = operations[i:i+chunk_size]
            result = await db["students"].bulk_write(chunk)
            print(f"  Processed {i + len(chunk)}/{len(operations)}")

    print("=== Hoàn tất migration ===")
    client.close()

asyncio.run(main())