"""Centralised notification creation.

Every producer (agents, orchestrators, the event checker, the create_reminder
tool, and the upcoming course-communication agent) goes through
`push_notification` so all notifications share one shape, a tz-aware
`created_at`, `send_at` scheduling (via notify_schedule), and optional per-type
dedup. This replaces the previously scattered, drift-prone insert sites.
"""
from datetime import datetime, timedelta, timezone


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def recently_fired(db, student_id: int, notif_type: str, hours: int = 24) -> bool:
    """True if a notification of this type was created within the window."""
    if db is None:
        return False
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    existing = await db.notifications.find_one({
        "student_id": student_id,
        "type": notif_type,
        "created_at": {"$gt": cutoff},
    })
    return existing is not None


async def push_notification(
    db,
    student_id: int,
    notif_type: str,
    title: str,
    body: str,
    action_options: list | None = None,
    dedup_hours: int | None = None,
) -> bool:
    """Insert one notification with a consistent shape + scheduling.

    Returns True if inserted, False if suppressed as a duplicate. When `db` is
    None (mock mode), logs and returns True. `dedup_hours` enables per-type
    dedup (None = no dedup).
    """
    from notify_schedule import compute_send_at

    if dedup_hours and await recently_fired(db, student_id, notif_type, dedup_hours):
        return False

    notif = {
        "student_id": student_id,
        "type": notif_type,
        "payload": {"title": title, "body": body},
        "action_options": action_options or [],
        "read": False,
        "created_at": now_iso(),
    }
    send_at = compute_send_at(notif_type)
    if send_at:
        notif["send_at"] = send_at

    if db is None:
        print(f"[notify] {notif_type} — {title}")
        return True
    await db.notifications.insert_one(notif)
    try:
        from db.utils import serialize_doc
        await db["notification"].insert_one(serialize_doc(notif))
    except Exception:
        pass
    return True
