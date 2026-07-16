from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import time
import os

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

    # Password check placeholder — integrate with university SSO/LDAP here
    # For now accept any non-empty password for known students
    if not req.password:
        raise HTTPException(status_code=401, detail="Password required")

    token = f"bearer_{req.student_id}_{int(time.time())}"
    return LoginResponse(access_token=token, student_id=req.student_id)
