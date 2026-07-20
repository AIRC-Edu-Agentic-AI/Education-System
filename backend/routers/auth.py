from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import time
import os
import bcrypt

from db.mongodb import db_state
from db.mock_data import MOCK_STUDENT

router = APIRouter()

class LoginRequest(BaseModel):
    student_id: int
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    student_id: int

@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    use_mock = os.getenv("USE_MOCK_DATA", "false").lower() == "true"

    if use_mock or not db_state.get("connected"):
        # Demo mode: accept any student_id + password
        token = f"demo_{req.student_id}_{int(time.time())}"
        return LoginResponse(access_token=token, student_id=req.student_id)

    # Real mode: verify student exists in DB
    db = db_state.get("db")
    student = await db["students"].find_one({"student_id": req.student_id})
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    if not req.password:
        raise HTTPException(status_code=401, detail="Password required")
        
    password_hash = student.get("password_hash")
    if not password_hash:
        raise HTTPException(status_code=401, detail="Invalid password")
        
    # Verify password
    try:
        if not bcrypt.checkpw(req.password.encode('utf-8'), password_hash.encode('utf-8')):
            raise HTTPException(status_code=401, detail="Invalid password")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid password")

    token = f"bearer_{req.student_id}_{int(time.time())}"
    return LoginResponse(access_token=token, student_id=req.student_id)