"""
Teacher Risk Management Router.

Handles:
- BR36: Lecturer xem danh sach SV co canh bao rui ro
- BR37: Lecturer gui tin nhan den tung SV hoac nhom SV theo muc rui ro
- BR40-42: AI Agent phan tich, de xuat danh sach SV can can thiep

Endpoints:
  GET  /api/risk/students          - Danh sach SV theo risk tier trong course
  GET  /api/risk/students/tier/{n} - Loc SV theo risk tier cu the
  POST /api/risk/notify            - Gui thong bao/tin nhan theo nhom rui ro
  GET  /api/risk/alerts            - Danh sach canh bao hien tai (intervention_alerts)
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from db.mongodb import db_state
from db.utils import serialize_doc

router = APIRouter()


def get_db():
    db = db_state.get("db")
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    return db


# ─── Pydantic Models ───────────────────────────────────────────────────────────

class RiskNotifyPayload(BaseModel):
    """Gui thong bao den nhom sinh vien theo risk tier."""
    module: str
    presentation: str
    risk_tiers: List[int]           # [1, 2, 3, 4] — gui den cac tier nay
    title: str
    content: str
    sender_role: str = "instructor"
    type: str = "intervention"      # intervention | warning | general_notice


class DirectRiskMessagePayload(BaseModel):
    """Gui tin nhan truc tiep den 1 sinh vien cu the."""
    student_id: int
    title: str
    content: str
    course_code: str
    sender_role: str = "instructor"
    type: str = "intervention"


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _risk_tier_label(tier: int) -> str:
    return {1: "Low", 2: "Medium", 3: "High", 4: "Critical"}.get(tier, "Unknown")


async def _get_students_by_risk(db, module: str, presentation: str, tiers: List[int] | None = None) -> List[Dict]:
    """
    Lay danh sach sinh vien voi risk data tu processed_students.
    Ket hop voi risk score tu students collection neu co.
    """
    query: Dict[str, Any] = {"code_module": module, "code_presentation": presentation}
    
    docs = await db["students"].find(
        {"enrollments.code_module": module, "enrollments.code_presentation": presentation},
        {
            "_id": 0,
            "student_id": 1,
            "full_name": 1,
            "email": 1,
            "risk": 1,
            "enrollments": 1
        }
    ).to_list(None)

    if not docs:
        return []

    result = []
    for d in docs:
        sid = d.get("student_id")
        risk_obj = d.get("risk", {})
        
        risk_score = risk_obj.get("score")
        risk_tier = risk_obj.get("tier")

        if risk_tier is None and risk_score is not None:
            if risk_score >= 0.8:
                risk_tier = 4
            elif risk_score >= 0.6:
                risk_tier = 3
            elif risk_score >= 0.4:
                risk_tier = 2
            else:
                risk_tier = 1

        if tiers and risk_tier not in tiers:
            continue

        result.append({
            "student_id": sid,
            "name": d.get("full_name") or f"Student {sid}",
            "email": d.get("email"),
            "risk_score": round(float(risk_score), 3) if risk_score is not None else None,
            "risk_tier": risk_tier,
            "risk_tier_label": _risk_tier_label(risk_tier) if risk_tier else None,
            "risk_flags": risk_obj.get("flags", []),
            "final_result": None,
            "vle_total": 0,
        })

    # Sort by risk_score desc (cao nhat len dau)
    result.sort(key=lambda x: (x.get("risk_score") or 0), reverse=True)
    return result


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/students")
async def get_risk_students(
    module: str = Query(..., description="Ma mon hoc"),
    presentation: str = Query(..., description="Hoc ky"),
    tier: Optional[int] = Query(None, ge=1, le=4, description="Loc theo tier (1-4)"),
) -> Dict[str, Any]:
    """
    BR36: Lay danh sach sinh vien co canh bao rui ro trong khoa hoc.
    Tra ve tat ca SV neu khong co filter tier, hoac chi SV theo tier cu the.
    """
    try:
        db = get_db()
        tiers = [tier] if tier else None
        students = await _get_students_by_risk(db, module, presentation, tiers)

        # Group by tier
        by_tier: Dict[int, List] = {1: [], 2: [], 3: [], 4: []}
        for s in students:
            t = s.get("risk_tier")
            if t and t in by_tier:
                by_tier[t].append(s)

        return {
            "module": module,
            "presentation": presentation,
            "total": len(students),
            "students": students,
            "summary": {
                "tier_1_low":      len(by_tier[1]),
                "tier_2_medium":   len(by_tier[2]),
                "tier_3_high":     len(by_tier[3]),
                "tier_4_critical": len(by_tier[4]),
            }
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.get("/students/tier/{tier_level}")
async def get_students_by_tier(
    tier_level: int,
    module: str = Query(...),
    presentation: str = Query(...),
) -> List[Dict[str, Any]]:
    """
    Lay danh sach SV theo 1 tier rui ro cu the.
    tier_level: 1=Low, 2=Medium, 3=High, 4=Critical
    """
    if tier_level not in (1, 2, 3, 4):
        raise HTTPException(status_code=400, detail="tier_level phai la 1, 2, 3, hoac 4")
    try:
        db = get_db()
        return await _get_students_by_risk(db, module, presentation, [tier_level])
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.post("/notify", status_code=201)
async def notify_risk_group(payload: RiskNotifyPayload) -> Dict[str, Any]:
    """
    BR37: Gui thong bao den tat ca SV thuoc cac risk tier duoc chon.
    
    Request body:
    {
        "module": "AAA",
        "presentation": "2013J",
        "risk_tiers": [3, 4],
        "title": "Can thien hoc tap",
        "content": "...",
        "type": "intervention"
    }
    """
    try:
        db = get_db()
        students = await _get_students_by_risk(db, payload.module, payload.presentation, payload.risk_tiers)
        
        if not students:
            return {"ok": True, "count": 0, "message": "Khong co sinh vien nao thuoc cac tier duoc chon"}

        now_iso = datetime.now(timezone.utc).isoformat()
        docs = [
            {
                "student_id": s["student_id"],
                "type": payload.type,
                "read": False,
                "sender_role": payload.sender_role,
                "course_code": payload.module,
                "is_broadcast_log": False,
                "payload": {
                    "title": payload.title,
                    "body": payload.content,
                },
                "created_at": now_iso,
            }
            for s in students
        ]

        if docs:
            result = await db["notifications"].insert_many(docs)
            inserted = len(result.inserted_ids)
        else:
            inserted = 0

        # Log broadcast
        broadcast_log = {
            "student_id": "teacher_broadcast",
            "recipient_id": "teacher_admin",
            "type": payload.type,
            "read": True,
            "sender_role": payload.sender_role,
            "course_code": payload.module,
            "is_broadcast_log": True,
            "target_count": inserted,
            "payload": {
                "title": f"[BROADCAST] {payload.title}",
                "body": f"Da gui den {inserted} sinh vien (Tier {payload.risk_tiers}): {payload.content}",
            },
            "created_at": now_iso,
        }
        await db["notifications"].insert_one(broadcast_log)

        return {
            "ok": True,
            "count": inserted,
            "risk_tiers": payload.risk_tiers,
            "module": payload.module,
            "presentation": payload.presentation,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.post("/notify/direct", status_code=201)
async def notify_student_direct(payload: DirectRiskMessagePayload) -> Dict[str, Any]:
    """
    BR37: Gui tin nhan truc tiep den 1 sinh vien cu the.
    """
    try:
        db = get_db()
        now_iso = datetime.now(timezone.utc).isoformat()
        doc = {
            "student_id": payload.student_id,
            "type": payload.type,
            "read": False,
            "sender_role": payload.sender_role,
            "course_code": payload.course_code,
            "is_broadcast_log": False,
            "payload": {
                "title": payload.title,
                "body": payload.content,
            },
            "created_at": now_iso,
        }
        result = await db["notifications"].insert_one(doc)
        return {"ok": True, "notification_id": str(result.inserted_id), "student_id": payload.student_id}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.get("/alerts")
async def get_intervention_alerts(
    module: Optional[str] = Query(None),
    presentation: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
) -> List[Dict[str, Any]]:
    """
    Lay danh sach canh bao can thiep (intervention_alerts collection).
    """
    try:
        db = get_db()
        query: Dict[str, Any] = {}
        if module:
            query["module"] = module
        if presentation:
            query["presentation"] = presentation

        docs = await db["intervention_alerts"].find(query).sort("created_at", -1).limit(limit).to_list(None)
        return serialize_doc(docs)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.get("/student/{student_id}/history")
async def get_student_risk_history(student_id: int) -> Dict[str, Any]:
    """Lay lich su bien dong risk score cua 1 sinh vien."""
    try:
        db = get_db()
        doc = await db["risk_history"].find_one({"student_id": student_id})
        if not doc:
            # Fallback: tinh tu students collection
            student = await db["students"].find_one(
                {"student_id": student_id},
                {"_id": 0, "risk": 1, "full_name": 1}
            )
            if not student:
                raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
            return {
                "student_id": student_id,
                "full_name": student.get("full_name"),
                "current_risk": student.get("risk", {}),
                "history": [],
            }
        return serialize_doc(doc)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc
