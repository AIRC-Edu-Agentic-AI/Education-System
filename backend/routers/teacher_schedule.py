from typing import Any, Dict, List
from bson import ObjectId

from fastapi import APIRouter, HTTPException
import traceback

from db.mongodb import db_state
from db.utils import serialize_doc
from routers.realtime_chat import manager as rtc_manager

router = APIRouter()


def get_db():
    db = db_state.get("db")
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    return db


@router.get("/schedules")
async def list_schedules() -> List[Dict[str, Any]]:
    try:
        db = get_db()
        docs = await db["timetable_blocks"].find({}).to_list(None)
        return serialize_doc(docs)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.post("/schedules", status_code=201)
async def create_schedule(payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        print(f"[SCHEDULE] create_schedule called. payload_type={type(payload)}")
        try:
            print(f"[SCHEDULE] payload keys={list(payload.keys())}")
        except Exception:
            print("[SCHEDULE] payload keys unavailable")
        db = get_db()
        print("[SCHEDULE] DB retrieved from db_state")
        payload.pop("_id", None)
        new_schedule = payload.pop("newSchedule", None)

        old_doc = None
        if "schedules" in payload:
            old_doc = await db["timetable_blocks"].find_one({})
            await db["timetable_blocks"].delete_many({})

        result = await db["timetable_blocks"].insert_one(payload)
        payload["_id"] = str(result.inserted_id)

        async def notify_students(item: Dict[str, Any], original: Dict[str, Any] | None = None, source: str = "schedule:create"):
            module = item.get("module")
            presentation = item.get("presentation")
            print(f"[SCHEDULE] notify_students called: source={source}, module={module!r}, presentation={presentation!r}")
            if not module or not presentation:
                print(f"[SCHEDULE] SKIP: module or presentation missing. item keys={list(item.keys())}")
                return

            students = await db["students"].find(
                {"enrollments.code_module": module, "enrollments.code_presentation": presentation},
                {"_id": 0, "student_id": 1}
            ).to_list(None)
            target_sids = [s.get("student_id") for s in students if "student_id" in s]
            print(f"[SCHEDULE] Found {len(target_sids)} enrolled students for {module}/{presentation}")
            if not target_sids:
                print(f"[SCHEDULE] SKIP: no enrolled students found")
                return

            from datetime import datetime, timezone
            now_iso = datetime.now(timezone.utc).isoformat()
            subject = item.get("subject") or (original and original.get("subject")) or "Class"
            new_date = item.get("date")
            new_start = item.get("startTime")
            new_end = item.get("endTime")
            new_room = item.get("room") or item.get("locationUrl") or "unknown room"

            if original:
                old_date = original.get("date")
                old_start = original.get("startTime")
                old_end = original.get("endTime")
                old_room = original.get("room") or original.get("locationUrl") or "unknown room"
                old_desc = f"{old_date or 'unknown date'} {old_start or ''}{('-' + old_end) if old_end else ''}".strip()
                new_desc = f"{new_date or 'unknown date'} {new_start or ''}{('-' + new_end) if new_end else ''}".strip()
                body_parts = [
                    f"Class \"{subject}\" has been updated: {old_desc} -> {new_desc}."
                ]
                if old_room != new_room:
                    body_parts.append(f"Room changed: {old_room} -> {new_room}.")
                else:
                    body_parts.append(f"Room: {new_room}.")
                title = "Class Schedule Updated"
            else:
                title = "New Class Scheduled"
                body_parts = [
                    f"A new class \"{subject}\" has been scheduled on {new_date} at {new_start}.",
                    f"Location: {new_room}."
                ]

            body = " ".join(body_parts)
            docs = [
                {
                    "student_id": sid,
                    "type": "general",
                    "read": False,
                    "sender_role": "instructor",
                    "course_code": module,
                    "payload": {
                        "title": title,
                        "body": body,
                    },
                    "created_at": now_iso,
                }
                for sid in target_sids
            ]
            if not docs:
                return
            await db["notifications"].insert_many(docs)
            # ── Realtime WebSocket push (mirrors teacher_notification.py) ──
            try:
                from bson import ObjectId as _OID
                # Build a single notification object in the same shape that
                # teacher_notification.py uses (which the student app already
                # parses correctly).
                instant_noti = {
                    "_id": str(_OID()),
                    "type": "general",
                    "read": False,
                    "sender_role": "instructor",
                    "senderRole": "Instructor",
                    "receiverRole": "Student",
                    "course_code": module,
                    "payload": {"title": title, "body": body},
                    "title": title,
                    "content": body,
                    "created_at": now_iso,
                    "createdAt": now_iso,
                    "is_broadcast_log": False,
                }
                print(f"[SCHEDULE] Pushing WS notification for {source}: title={title!r}, "
                      f"target_sids={target_sids}")

                # 1. Send to teacher dashboard
                await rtc_manager.send_to_user("teacher_admin", {
                    "type": "new_notification",
                    "notification": {**instant_noti, "is_broadcast_log": True},
                })
                # 2. Send only to enrolled students for this module/presentation
                for sid in target_sids:
                    await rtc_manager.send_to_user(str(sid), {
                        "type": "new_notification",
                        "notification": {**instant_noti, "student_id": sid},
                    })
            except Exception:
                print(f"[SCHEDULE] Failed to push realtime notifications for {source}")
                traceback.print_exc()

        print(f"[SCHEDULE] newSchedule={new_schedule is not None}, "
              f"module={new_schedule.get('module') if new_schedule else None!r}, "
              f"presentation={new_schedule.get('presentation') if new_schedule else None!r}")
        if new_schedule and new_schedule.get("module") and new_schedule.get("presentation"):
            await notify_students(new_schedule, None, "schedule:create")
        elif new_schedule:
            print(f"[SCHEDULE] WARN: newSchedule present but missing module/presentation. keys={list(new_schedule.keys())}")

        if old_doc and "schedules" in payload:
            old_items = {str(item.get("id")): item for item in old_doc.get("schedules", []) if item.get("id")}
            new_items = {str(item.get("id")): item for item in payload.get("schedules", []) if item.get("id")}
            for item_id, new_item in new_items.items():
                old_item = old_items.get(item_id)
                if old_item and new_item != old_item:
                    await notify_students(new_item, old_item, "schedule:update")

        return serialize_doc(payload)
    except HTTPException:
        raise
    except Exception as exc:
        print("[SCHEDULE] Exception in create_schedule:")
        traceback.print_exc()
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.put("/schedules/{schedule_id}")
async def update_schedule(schedule_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        db = get_db()
        payload.pop("_id", None)
        # Fetch original document to include old values in notifications
        original = await db["timetable_blocks"].find_one({"_id": ObjectId(schedule_id)})
        result = await db["timetable_blocks"].update_one(
            {"_id": ObjectId(schedule_id)}, {"$set": payload}
        )

        # If an update occurred, notify enrolled students about the change
        if result.modified_count and original:
            updated = await db["timetable_blocks"].find_one({"_id": ObjectId(schedule_id)})

            # Prefer module/presentation from updated doc, fallback to payload or original
            module = (updated or {}).get("module") or payload.get("module") or original.get("module")
            presentation = (updated or {}).get("presentation") or payload.get("presentation") or original.get("presentation")

            if module and presentation:
                students = await db["students"].find(
                    {"enrollments.code_module": module, "enrollments.code_presentation": presentation},
                    {"_id": 0, "student_id": 1}
                ).to_list(None)
                target_sids = [s.get("student_id") for s in students if "student_id" in s]

                if target_sids:
                    try:
                        from datetime import datetime, timezone
                        now_iso = datetime.now(timezone.utc).isoformat()

                        # Build a human readable diff message
                        old_date = original.get("date")
                        old_start = original.get("startTime")
                        old_end = original.get("endTime")
                        new_date = (updated or {}).get("date")
                        new_start = (updated or {}).get("startTime")
                        new_end = (updated or {}).get("endTime")

                        old_room = original.get("room") or original.get("location")
                        new_room = (updated or {}).get("room") or (updated or {}).get("location")

                        subject = (updated or {}).get("subject") or original.get("subject") or "Class"

                        if old_date or old_start or old_end:
                            old_desc = f"{old_date or 'unknown date'} {old_start or ''}{('-' + old_end) if old_end else ''}".strip()
                        else:
                            old_desc = "previous time"

                        new_desc = f"{new_date or 'unknown date'} {new_start or ''}{('-' + new_end) if new_end else ''}".strip()

                        body_parts = [f"Schedule updated for \"{subject}\": {old_desc} -> {new_desc}."]
                        # Include room/location change if present
                        if old_room or new_room:
                            if old_room != new_room:
                                body_parts.append(f"Room changed: {old_room or 'unknown'} -> {new_room or 'unknown'}.")
                            else:
                                body_parts.append(f"Room: {new_room or old_room}")

                        body = " ".join(body_parts)

                        docs = [
                            {
                                "student_id": sid,
                                "type": "general",
                                "read": False,
                                "sender_role": "instructor",
                                "course_code": module,
                                "payload": {
                                    "title": "Class Schedule Updated",
                                    "body": body,
                                },
                                "created_at": now_iso,
                            }
                            for sid in target_sids
                        ]
                        if docs:
                            await db["notifications"].insert_many(docs)
                            # ── Realtime WS push (same as create_schedule) ──
                            try:
                                import asyncio
                                from bson import ObjectId as _OID
                                update_title = "Class Schedule Updated"
                                instant_noti = {
                                    "_id": str(_OID()),
                                    "type": "general",
                                    "read": False,
                                    "sender_role": "instructor",
                                    "senderRole": "Instructor",
                                    "receiverRole": "Student",
                                    "course_code": module,
                                    "payload": {"title": update_title, "body": body},
                                    "title": update_title,
                                    "content": body,
                                    "created_at": now_iso,
                                    "createdAt": now_iso,
                                    "is_broadcast_log": False,
                                }
                                print(f"[SCHEDULE] Pushing WS notification for update: "
                                      f"target_sids={target_sids}")
                                await rtc_manager.send_to_user("teacher_admin", {
                                    "type": "new_notification",
                                    "notification": {**instant_noti, "is_broadcast_log": True},
                                })
                                for sid in target_sids:
                                    await rtc_manager.send_to_user(str(sid), {
                                        "type": "new_notification",
                                        "notification": {**instant_noti, "student_id": sid},
                                    })
                            except Exception:
                                print("[SCHEDULE] Failed to push realtime notifications for update")
                                traceback.print_exc()
                    except Exception:
                        print("[SCHEDULE] Failed to send update notifications")
                        traceback.print_exc()

        return {"updated": result.modified_count}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid schedule id: {exc}") from exc


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str) -> Dict[str, Any]:
    try:
        db = get_db()
        result = await db["timetable_blocks"].delete_one({"_id": ObjectId(schedule_id)})
        return {"deleted": result.deleted_count}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid schedule id: {exc}") from exc


@router.get("/classes")
async def list_classes() -> List[str]:
    try:
        db = get_db()
        courses = await db["processed_courses"].find(
            {}, {"module": 1, "presentation": 1, "_id": 0}
        ).to_list(None)
        return sorted({
            f"{c.get('module')}-{c.get('presentation')}"
            for c in courses
            if c.get("module") and c.get("presentation")
        })
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc


@router.get("/rooms")
async def list_rooms() -> List[str]:
    return [
        "G2-101", "G2-102", "G2-103",
        "G2-201", "G2-202", "G2-203",
        "E3-101", "E3-102",
        "E3-201", "E3-202", "E3-301", "E3-302",
        "B1-101", "B1-102", "B1-201", "B1-202",
        "Online - Zoom", "Online - Teams",
    ]
