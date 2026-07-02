"""Audit logging for course communication."""

from .utils import now_iso


async def record_audit(db, action: str, course_code: str | None, user_id: int | None, metadata: dict | None = None):
    """Record an audit log entry."""
    await db.audit_logs.insert_one({
        "action": action,
        "course_code": course_code,
        "user_id": user_id,
        "metadata": metadata or {},
        "created_at": now_iso(),
    })