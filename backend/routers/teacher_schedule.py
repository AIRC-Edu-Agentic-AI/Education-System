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


async def notify_students(
    item: Dict[str, Any],
    original: Dict[str, Any] | None = None,
    source: str = "schedule:create",
):
    """
    Notify enrolled students about a created or updated schedule item,
    and broadcast schedule_updated to all active WebSocket clients.
    """
    try:
        db = get_db()
        module = item.get("module") or (original and original.get("module"))
        presentation = item.get("presentation") or (original and original.get("presentation"))
        print(f"[SCHEDULE] notify_students called: source={source}, module={module!r}, presentation={presentation!r}")

        from datetime import datetime, timezone
        from bson import ObjectId as _OID

        now_iso = datetime.now(timezone.utc).isoformat()
        subject = (
            item.get("subject")
            or item.get("activity")
            or (original and (original.get("subject") or original.get("activity")))
            or "Class"
        )
        new_date = item.get("date") or (original and original.get("date")) or ""
        new_start = item.get("startTime") or (original and original.get("startTime")) or ""
        new_end = item.get("endTime") or (original and original.get("endTime")) or ""
        new_room = (
            item.get("room")
            or item.get("locationUrl")
            or item.get("location")
            or (original and (original.get("room") or original.get("locationUrl") or original.get("location")))
            or "room"
        )

        if source == "schedule:update" and original:
            old_date = original.get("date") or ""
            old_start = original.get("startTime") or ""
            old_end = original.get("endTime") or ""
            old_room = original.get("room") or original.get("locationUrl") or original.get("location") or "room"
            old_desc = f"{old_date or 'previous date'} {old_start}{('-' + old_end) if old_end else ''}".strip()
            new_desc = f"{new_date or 'new date'} {new_start}{('-' + new_end) if new_end else ''}".strip()
            body_parts = [
                f'Class "{subject}" has been updated: {old_desc} -> {new_desc}.'
            ]
            if old_room != new_room:
                body_parts.append(f"Room changed: {old_room} -> {new_room}.")
            elif new_room:
                body_parts.append(f"Room: {new_room}.")
            title = "Class Schedule Updated"
        elif source == "schedule:update":
            time_desc = f"{new_date} {new_start}{('-' + new_end) if new_end else ''}".strip()
            title = "Class Schedule Updated"
            body_parts = [
                f'Class "{subject}" schedule has been updated to {time_desc}.',
                f"Location: {new_room}.",
            ]
        else:
            title = "New Class Scheduled"
            body_parts = [
                f'A new class "{subject}" has been scheduled on {new_date} at {new_start}.',
                f"Location: {new_room}.",
            ]

        body = " ".join(body_parts)

        target_sids = []
        if module and presentation:
            students = await db["students"].find(
                {"enrollments.code_module": module, "enrollments.code_presentation": presentation},
                {"_id": 0, "student_id": 1}
            ).to_list(None)
            target_sids = [s.get("student_id") for s in students if "student_id" in s]
            print(f"[SCHEDULE] Found {len(target_sids)} enrolled students for {module}/{presentation}")

        # Insert notification records in DB if enrolled students found
        if target_sids:
            docs = [
                {
                    "student_id": sid,
                    "type": "general",
                    "read": False,
                    "sender_role": "instructor",
                    "course_code": module or "General",
                    "payload": {
                        "title": title,
                        "body": body,
                    },
                    "created_at": now_iso,
                }
                for sid in target_sids
            ]
            await db["notifications"].insert_many(docs)

        # Build instant notification object for WebSocket
        instant_noti = {
            "_id": str(_OID()),
            "type": "general",
            "read": False,
            "sender_role": "instructor",
            "senderRole": "Instructor",
            "receiverRole": "Student",
            "course_code": module or "General",
            "payload": {"title": title, "body": body},
            "title": title,
            "content": body,
            "created_at": now_iso,
            "createdAt": now_iso,
            "is_broadcast_log": False,
        }

        # 1. Send notification to teacher dashboard
        await rtc_manager.send_to_user("teacher_admin", {
            "type": "new_notification",
            "notification": {**instant_noti, "is_broadcast_log": True},
        })

        # 2. Send notification to enrolled students
        for sid in target_sids:
            await rtc_manager.send_to_user(str(sid), {
                "type": "new_notification",
                "notification": {**instant_noti, "student_id": sid},
            })

        # 3. Send schedule_updated event to enrolled students
        for sid in target_sids:
            await rtc_manager.send_to_user(str(sid), {
                "type": "schedule_updated",
                "module": module,
                "presentation": presentation,
            })

        # 4. Broadcast schedule_updated to ALL active WebSocket connections (student clients)
        active_uids = list(rtc_manager.active_connections.keys())
        for uid in active_uids:
            if uid != "teacher_admin" and uid not in [str(s) for s in target_sids]:
                await rtc_manager.send_to_user(uid, {
                    "type": "schedule_updated",
                    "module": module,
                    "presentation": presentation,
                })
        print(f"[SCHEDULE] [OK] schedule_updated broadcasted for {source} (module={module}, pres={presentation})")

    except Exception as exc:
        print(f"[SCHEDULE] Error in notify_students ({source}): {exc}")
        traceback.print_exc()


async def notify_students_deleted(item: Dict[str, Any]):
    """Send a cancellation notification and broadcast schedule_updated event."""
    try:
        db = get_db()
        module = item.get("module")
        presentation = item.get("presentation")

        from datetime import datetime, timezone
        from bson import ObjectId as _OID

        now_iso = datetime.now(timezone.utc).isoformat()
        subject = item.get("subject") or item.get("activity") or "Class"
        del_date = item.get("date") or "unknown date"
        del_start = item.get("startTime") or ""
        del_end = item.get("endTime") or ""
        del_room = item.get("room") or item.get("locationUrl") or item.get("location") or "room"
        time_desc = f"{del_date} {del_start}{('-' + del_end) if del_end else ''}".strip()
        title = "Class Cancelled"
        body = f'Class "{subject}" scheduled for {time_desc} at {del_room} has been cancelled.'

        target_sids = []
        if module and presentation:
            students = await db["students"].find(
                {"enrollments.code_module": module, "enrollments.code_presentation": presentation},
                {"_id": 0, "student_id": 1}
            ).to_list(None)
            target_sids = [s.get("student_id") for s in students if "student_id" in s]

        if target_sids:
            docs = [
                {
                    "student_id": sid,
                    "type": "general",
                    "read": False,
                    "sender_role": "instructor",
                    "course_code": module or "General",
                    "payload": {"title": title, "body": body},
                    "created_at": now_iso,
                }
                for sid in target_sids
            ]
            await db["notifications"].insert_many(docs)

        instant_noti = {
            "_id": str(_OID()),
            "type": "general",
            "read": False,
            "sender_role": "instructor",
            "senderRole": "Instructor",
            "receiverRole": "Student",
            "course_code": module or "General",
            "payload": {"title": title, "body": body},
            "title": title,
            "content": body,
            "created_at": now_iso,
            "createdAt": now_iso,
            "is_broadcast_log": False,
        }

        # 1. Send notification to teacher dashboard
        await rtc_manager.send_to_user("teacher_admin", {
            "type": "new_notification",
            "notification": {**instant_noti, "is_broadcast_log": True},
        })

        # 2. Send notification to enrolled students
        for sid in target_sids:
            await rtc_manager.send_to_user(str(sid), {
                "type": "new_notification",
                "notification": {**instant_noti, "student_id": sid},
            })

        # 3. Send schedule_updated event to enrolled students
        for sid in target_sids:
            await rtc_manager.send_to_user(str(sid), {
                "type": "schedule_updated",
                "module": module,
                "presentation": presentation,
            })

        # 4. Broadcast schedule_updated to ALL active connections
        active_uids = list(rtc_manager.active_connections.keys())
        for uid in active_uids:
            if uid != "teacher_admin" and uid not in [str(s) for s in target_sids]:
                await rtc_manager.send_to_user(uid, {
                    "type": "schedule_updated",
                    "module": module,
                    "presentation": presentation,
                })
        print(f"[SCHEDULE] [OK] schedule_updated (cancel) broadcasted for {subject!r}")

    except Exception as exc:
        print(f"[SCHEDULE] Exception in notify_students_deleted: {exc}")
        traceback.print_exc()


@router.post("/schedules", status_code=201)
async def create_schedule(payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        print(f"[SCHEDULE] create_schedule called. payload_type={type(payload)}")
        db = get_db()
        payload.pop("_id", None)
        new_schedule = payload.pop("newSchedule", None)
        updated_schedule = payload.pop("updatedSchedule", None)
        deleted_schedule_id = payload.pop("deletedScheduleId", None)
        deleted_schedule_data = payload.pop("deletedScheduleData", None)

        old_doc = None
        if "schedules" in payload:
            old_doc = await db["timetable_blocks"].find_one({})
            await db["timetable_blocks"].delete_many({})

        result = await db["timetable_blocks"].insert_one(payload)
        payload["_id"] = str(result.inserted_id)

        # 1. Handle explicitly added new schedule
        if new_schedule and isinstance(new_schedule, dict):
            await notify_students(new_schedule, None, "schedule:create")

        # 2. Handle explicitly updated schedule
        if updated_schedule and isinstance(updated_schedule, dict):
            original_item = None
            if old_doc and "schedules" in old_doc:
                for item in old_doc.get("schedules", []):
                    if str(item.get("id")) == str(updated_schedule.get("id")):
                        original_item = item
                        break
            await notify_students(updated_schedule, original_item, "schedule:update")

        # 3. Diff old vs new schedules to catch any other edits or deletions
        if old_doc and "schedules" in payload:
            old_items = {str(item.get("id")): item for item in old_doc.get("schedules", []) if item.get("id")}
            new_items = {str(item.get("id")): item for item in payload.get("schedules", []) if item.get("id")}

            handled_update_id = str(updated_schedule.get("id")) if updated_schedule and isinstance(updated_schedule, dict) else None
            handled_delete_id = str((deleted_schedule_data or {}).get("id") or deleted_schedule_id) if (deleted_schedule_data or deleted_schedule_id) else None

            # Detect unhandled modified items
            for item_id, new_item in new_items.items():
                if item_id == handled_update_id:
                    continue
                old_item = old_items.get(item_id)
                if old_item and new_item != old_item:
                    await notify_students(new_item, old_item, "schedule:update")

            # Detect unhandled deleted items
            deleted_ids = set(old_items.keys()) - set(new_items.keys())
            for del_id in deleted_ids:
                if del_id == handled_delete_id:
                    continue
                del_item = old_items[del_id]
                await notify_students_deleted(del_item)

        # 4. Handle explicitly deleted schedule
        if deleted_schedule_data and isinstance(deleted_schedule_data, dict):
            await notify_students_deleted(deleted_schedule_data)
        elif deleted_schedule_id:
            await notify_students_deleted({"id": deleted_schedule_id})

        # 5. Always ensure all active clients refresh
        for uid in list(rtc_manager.active_connections.keys()):
            if uid != "teacher_admin":
                await rtc_manager.send_to_user(uid, {"type": "schedule_updated"})

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
        original = await db["timetable_blocks"].find_one({"_id": ObjectId(schedule_id)})
        result = await db["timetable_blocks"].update_one(
            {"_id": ObjectId(schedule_id)}, {"$set": payload}
        )

        updated = await db["timetable_blocks"].find_one({"_id": ObjectId(schedule_id)})
        await notify_students(updated or payload, original, "schedule:update")

        return {"updated": result.modified_count}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid schedule id: {exc}") from exc


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str) -> Dict[str, Any]:
    try:
        db = get_db()
        doc = await db["timetable_blocks"].find_one({"_id": ObjectId(schedule_id)})
        result = await db["timetable_blocks"].delete_one({"_id": ObjectId(schedule_id)})
        if doc:
            schedules_list = doc.get("schedules") if isinstance(doc.get("schedules"), list) else None
            if schedules_list:
                for item in schedules_list:
                    if isinstance(item, dict):
                        await notify_students_deleted(item)
            else:
                await notify_students_deleted(doc)
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
