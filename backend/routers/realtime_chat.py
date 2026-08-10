from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import json
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from db.mongodb import db_state
from db.utils import serialize_doc

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_to_user(self, user_id: str, message: dict):
        if user_id not in self.active_connections:
            return
        msg_type = message.get("type", "unknown")
        for connection in self.active_connections[user_id]:
            try:
                await connection.send_json(message)
                print(f"[WS] ✓ Sent {msg_type} to user={user_id}")
            except Exception as e:
                print(f"[WS] ✗ Failed to send {msg_type} to user={user_id}: {e}")


    async def broadcast_to_channel(self, channel: dict, message: dict):
        if "members" in channel and channel["members"]:
            for member in channel["members"]:
                await self.send_to_user(str(member), message)
            # Ensure teacher always receives messages in private groups too if they are monitoring
            await self.send_to_user("teacher_admin", message)
        else:
            # Global channel: broadcast to all connected users
            for user_id in list(self.active_connections.keys()):
                await self.send_to_user(user_id, message)

import asyncio

manager = ConnectionManager()

async def listen_to_change_stream():
    """Listen to MongoDB Atlas Change Stream so multiple Uvicorn instances automatically sync WebSockets in real time across any machines!"""
    while True:
        try:
            db = db_state.get("db")
            if db is None:
                await asyncio.sleep(2)
                continue
            
            async with db.messages.watch(full_document="updateLookup") as stream:
                print("[WS ChangeStream] Started listening to MongoDB messages changes...")
                async for change in stream:
                    if change.get("operationType") in ["insert", "update", "replace"]:
                        doc = change.get("fullDocument")
                        if not doc:
                            continue
                        
                        channel_id = str(doc.get("channel_id"))
                        query_list = [{"_id": channel_id}]
                        try:
                            query_list.append({"_id": ObjectId(channel_id)})
                        except Exception:
                            pass
                        channel = await db["channels"].find_one({"$or": query_list})
                        
                        serialized_msg = serialize_doc(doc)
                        broadcast_data = {"type": "new_message", "message": serialized_msg}
                        
                        if channel:
                            await manager.broadcast_to_channel(channel, broadcast_data)
                        else:
                            for uid in list(manager.active_connections.keys()):
                                await manager.send_to_user(uid, broadcast_data)
        except Exception as e:
            print(f"[WS ChangeStream Error] {e}, retrying in 3s...")
            await asyncio.sleep(3)

def get_db():
    db = db_state.get("db")
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    return db

class CreateChannelPayload(BaseModel):
    name: str
    course_code: str
    members: List[str]
    type: str = "class_group"
    
@router.post("/channels")
async def create_channel(payload: CreateChannelPayload) -> Dict[str, Any]:
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()
    normalized_members = [str(m) for m in payload.members]

    doc = {
        "course_code": payload.course_code,
        "type": payload.type,
        "name": payload.name,
        "is_read_only": False,
        "allowed_post_roles": ["instructor", "student", "class_rep"],
        "status": "active",
        "members": normalized_members,
        "created_at": now,
        "updated_at": now
    }

    if payload.type == "private_message":
        mem_strs = sorted(normalized_members)
        members_key = "|".join(mem_strs)
        doc["members_key"] = members_key

        # Check existing first before attempting insert
        existing = await db["channels"].find_one({
            "type": "private_message",
            "members_key": members_key
        })
        if existing:
            return serialize_doc(existing)

        try:
            result = await db["channels"].insert_one(doc)
            doc["_id"] = result.inserted_id
        except DuplicateKeyError:
            existing = await db["channels"].find_one({
                "type": "private_message",
                "members_key": members_key
            })
            return serialize_doc(existing)
    else:
        result = await db["channels"].insert_one(doc)
        doc["_id"] = result.inserted_id

    serialized_doc = serialize_doc(doc)
    msg = {"type": "channel_created", "channel": serialized_doc}
    for member in payload.members:
        await manager.send_to_user(str(member), msg)

    return serialized_doc

@router.get("/channels")
async def get_channels(user_id: str, course_code: Optional[str] = None) -> List[Dict[str, Any]]:
    db = get_db()
    
    if course_code:
        try:
            from db.course_communication.channel import _ensure_course_channels
            await _ensure_course_channels(db, course_code)
        except Exception as e:
            print(f"Error seeding channels for {course_code}: {e}")

    if course_code:
        query = {
            "$or": [
                {"members": user_id},
                {
                    "course_code": course_code,
                    "type": {"$in": ["announcement", "discussion", "class_group"]},
                    "$or": [
                        {"members": {"$exists": False}},
                        {"members": {"$size": 0}},
                        {"members": None}
                    ]
                }
            ]
        }
    else:
        query = {"members": user_id}
        
    docs = await db["channels"].find(query).sort("created_at", -1).to_list(None)
    
    # Deduplicate private_message channels by sorted members key
    unique_docs = []
    seen_private_keys = set()
    for doc in docs:
        if doc.get("type") == "private_message":
            mems = sorted(str(m) for m in doc.get("members", []))
            key = "|".join(mems)
            if key in seen_private_keys:
                continue
            seen_private_keys.add(key)
        unique_docs.append(doc)

    # Inject Legacy Broadcasts channel for backward compatibility
    legacy_channel = {
        "_id": "legacy_broadcasts",
        "course_code": course_code or "ALL",
        "type": "announcement",
        "name": "Lịch sử Thông báo Cũ",
        "members": [user_id],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    unique_docs.append(legacy_channel)
    
    return serialize_doc(unique_docs)

@router.get("/channels/{channel_id}/messages")
async def get_messages(channel_id: str, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
    db = get_db()
    if channel_id == "legacy_broadcasts":
        # Fetch old notifications
        old_notifs = await db["notifications"].find({"is_broadcast_log": True}).sort("createdAt", -1).skip(skip).limit(limit).to_list(None)
        messages = []
        for n in old_notifs:
            messages.append({
                "_id": str(n["_id"]),
                "channel_id": "legacy_broadcasts",
                "sender_id": n.get("senderRole", "Instructor"),
                "sender_role": "instructor",
                "content": f"[{n.get('type', 'broadcast').upper()}] {n.get('title', '')}\n{n.get('content', '')}",
                "created_at": n.get("createdAt", n.get("created_at", datetime.now(timezone.utc).isoformat()))
            })
        messages.reverse()
        return messages

    target_ids = [channel_id]
    if str(channel_id).startswith("private_"):
        sid_str = str(channel_id).replace("private_", "")
        chan = await db["channels"].find_one({
            "type": "private_message",
            "members": {"$all": ["teacher_admin", sid_str]}
        })
        if not chan:
            mem_strs = sorted(["teacher_admin", sid_str])
            chan = await db["channels"].find_one({
                "type": "private_message",
                "members_key": "|".join(mem_strs)
            })
        if chan:
            target_ids.append(str(chan["_id"]))

    channel_query = []
    for tid in target_ids:
        channel_query.append({"channel_id": tid})
        try:
            channel_query.append({"channel_id": ObjectId(tid)})
        except Exception:
            pass
        
    docs = await db["messages"].find({"$or": channel_query, "parent_id": None}).sort("created_at", -1).skip(skip).limit(limit).to_list(None)
    docs.reverse()
    for d in docs:
        d["_id"] = str(d["_id"])
        d["channel_id"] = str(d["channel_id"])
    return serialize_doc(docs)

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    db = db_state.get("db")
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg_data = json.loads(data)
                channel_id = msg_data.get("channel_id")
                content = msg_data.get("content")
                sender_role = msg_data.get("sender_role", "student")
                sender_id_int = None
                try:
                    sender_id_int = int(user_id)
                except ValueError:
                    sender_id_int = user_id
                
                if channel_id and content and db is not None:
                    if channel_id == "legacy_broadcasts":
                        continue # read only
                    
                    real_chan_id = channel_id
                    if str(channel_id).startswith("private_"):
                        sid_str = str(channel_id).replace("private_", "")
                        c = await db["channels"].find_one({
                            "type": "private_message",
                            "members": {"$all": ["teacher_admin", sid_str]}
                        })
                        if c:
                            real_chan_id = str(c["_id"])

                    query_list = [{"_id": real_chan_id}]
                    try:
                        query_list.append({"_id": ObjectId(real_chan_id)})
                    except Exception:
                        pass
                    
                    channel = await db["channels"].find_one({"$or": query_list})
                    if not channel:
                        print(f"[WS] Channel not found for ID: {channel_id}")
                        continue
                        
                    doc = {
                        "channel_id": channel["_id"],
                        "course_code": channel.get("course_code"),
                        "channel_type": channel.get("type", "discussion"),
                        "sender_id": sender_id_int,
                        "sender_role": sender_role,
                        "content": content,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "parent_id": None,
                        "reactions": []
                    }
                    result = await db["messages"].insert_one(doc)
                    doc["_id"] = result.inserted_id
                    serialized_msg = serialize_doc(doc)
                    
                    broadcast_data = {"type": "new_message", "message": serialized_msg}
                    
                    await manager.broadcast_to_channel(channel, broadcast_data)
                        
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

@router.get("/private-channel")
async def get_private_channel(student_id: str, course_code: Optional[str] = None) -> Dict[str, Any]:
    """Get or create a private message channel between instructor and a specific student."""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database required")
    sid_str = str(student_id)
    sid_int = int(student_id) if student_id.isdigit() else student_id

    mem_strs = sorted(["teacher_admin", sid_str])
    members_key = "|".join(mem_strs)

    # 1. Search by members_key
    chan = await db["channels"].find_one({
        "type": "private_message",
        "members_key": members_key
    })
    
    if not chan:
        # 2. Search by members array fallback
        chans = await db["channels"].find({
            "type": "private_message",
            "members": {"$all": ["teacher_admin"]}
        }).to_list(100)
        for c in chans:
            mems = [str(m) for m in c.get("members", [])]
            if sid_str in mems or str(sid_int) in mems:
                chan = c
                # Ensure members_key is updated in DB
                await db["channels"].update_one({"_id": chan["_id"]}, {"$set": {"members_key": members_key}})
                chan["members_key"] = members_key
                break

    if not chan:
        student_doc = await db["students"].find_one({"$or": [{"student_id": sid_int}, {"student_id": sid_str}]})
        student_name = student_doc.get("full_name", f"Sinh viên {student_id}") if student_doc else f"Sinh viên {student_id}"
        now = datetime.now(timezone.utc).isoformat()
        new_chan = {
            "name": student_name,
            "course_code": course_code or "AAA 2013J",
            "members": ["teacher_admin", sid_str],
            "members_key": members_key,
            "type": "private_message",
            "status": "active",
            "created_at": now,
            "updated_at": now
        }
        try:
            res = await db["channels"].insert_one(new_chan)
            new_chan["_id"] = res.inserted_id
            chan = new_chan
        except DuplicateKeyError:
            chan = await db["channels"].find_one({
                "type": "private_message",
                "members_key": members_key
            })
        
    return serialize_doc(chan)