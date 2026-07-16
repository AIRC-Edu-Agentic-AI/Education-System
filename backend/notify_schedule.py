"""Notification scheduling / dispatch.

When enabled, non-urgent notifications get a future `send_at` so they're spread
across the day instead of arriving all at once. The GET /notify endpoint hides
notifications whose `send_at` is still in the future — that query-time filter is
the "dispatcher" (no extra background job needed; clients poll and they surface
when due).

Disabled by default → every notification is immediate (current behaviour, so
rapid testing is unaffected). The demo forces an immediate window so "Run Demo"
stays instant even when scheduling is on.
"""
from datetime import datetime, timedelta, timezone

# Urgent types always go out immediately, regardless of scheduling.
URGENT_TYPES = {
    "deadline_critical", "risk_intervention", "assessment_shock", "wellbeing",
}

# Per-type position within the spread window (fraction of spread_minutes).
_TYPE_FRACTION = {
    "reminder": 0.0,            # morning briefing
    "assessment_update": 0.1,
    "deadline_warning": 0.15,
    "milestone_check": 0.2,
    "vle_inactivity": 0.3,
    "progress_check": 0.35,
    "course_guidance": 0.5,
    "intervention": 0.5,
    "progress_report": 0.8,
}
_DEFAULT_FRACTION = 0.25

_settings = {
    "enabled": False,        # opt-in; off = everything immediate
    "spread_minutes": 240,   # window over which notifications are spread
    "tz_offset_hours": 7,    # student local tz (for quiet hours) — Hanoi default
    "quiet_start": 22,       # no sends 22:00–07:00 local
    "quiet_end": 7,
}
_immediate_until: datetime | None = None


def get_settings() -> dict:
    return dict(_settings)


def set_settings(enabled: bool | None = None, spread_minutes: int | None = None) -> dict:
    if enabled is not None:
        _settings["enabled"] = bool(enabled)
    if spread_minutes is not None:
        _settings["spread_minutes"] = max(0, int(spread_minutes))
    return get_settings()


def force_immediate(seconds: int = 180) -> None:
    """Send everything immediately for the next `seconds` (used by Run Demo)."""
    global _immediate_until
    _immediate_until = datetime.now(timezone.utc) + timedelta(seconds=seconds)


# ── Persistence (survive backend restarts) ──────────────────────────────────────

_SETTINGS_ID = "notify_schedule"


async def load_settings() -> None:
    """Load persisted settings from DB at startup (in-memory defaults otherwise)."""
    from db.mongodb import get_db
    db = get_db()
    if db is None:
        return
    doc = await db.app_settings.find_one({"_id": _SETTINGS_ID})
    if doc:
        _settings["enabled"] = bool(doc.get("enabled", _settings["enabled"]))
        _settings["spread_minutes"] = int(doc.get("spread_minutes", _settings["spread_minutes"]))
        print(f"[notify_schedule] Loaded settings: {get_settings()}")


async def save_settings_db() -> None:
    from db.mongodb import get_db
    db = get_db()
    if db is None:
        return
    await db.app_settings.update_one(
        {"_id": _SETTINGS_ID},
        {"$set": {"enabled": _settings["enabled"],
                  "spread_minutes": _settings["spread_minutes"]}},
        upsert=True,
    )


def _clamp_quiet(dt_utc: datetime) -> datetime:
    off = timedelta(hours=_settings["tz_offset_hours"])
    local = dt_utc + off
    qs, qe = _settings["quiet_start"], _settings["quiet_end"]
    if local.hour >= qs or local.hour < qe:
        base = local + timedelta(days=1) if local.hour >= qs else local
        local = base.replace(hour=qe, minute=0, second=0, microsecond=0)
        dt_utc = local - off
    return dt_utc


def compute_send_at(notif_type: str) -> str | None:
    """Return an ISO send time, or None for 'send immediately'."""
    now = datetime.now(timezone.utc)
    if not _settings["enabled"]:
        return None
    if _immediate_until and now < _immediate_until:
        return None
    if notif_type in URGENT_TYPES:
        return None
    frac = _TYPE_FRACTION.get(notif_type, _DEFAULT_FRACTION)
    target = now + timedelta(minutes=_settings["spread_minutes"] * frac)
    return _clamp_quiet(target).isoformat()
