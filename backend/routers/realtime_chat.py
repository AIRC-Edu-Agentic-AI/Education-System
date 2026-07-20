from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import json
from bson import ObjectId

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
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

manager = ConnectionManager()

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
    doc = {
        "course_code": payload.course_code,
        "type": payload.type,
        "name": payload.name,
        "is_read_only": False,
        "allowed_post_roles": ["instructor", "student", "class_rep"],
        "status": "active",
        "members": payload.members,
        "created_at": now,
        "updated_at": now
    }
    result = await db["channels"].insert_one(doc)
    doc["_id"] = result.inserted_id
    serialized_doc = serialize_doc(doc)
    
    msg = {"type": "channel_created", "channel": serialized_doc}
    for member in payload.members:
        await manager.send_to_user(member, msg)
        
    return serialized_doc

@router.get("/channels")
async def get_channels(user_id: str, course_code: Optional[str] = None) -> List[Dict[str, Any]]:
    db = get_db()
    query = {"$or": [{"members": user_id}]}
    if course_code:
        query["$or"].append({"course_code": course_code})
        
    docs = await db["channels"].find(query).sort("created_at", -1).to_list(None)
    
    # Inject Legacy Broadcasts channel for backward compatibility
    legacy_channel = {
        "_id": "legacy_broadcasts",
        "course_code": course_code or "ALL",
        "type": "announcement",
        "name": "Lịch sử Thông báo Cũ",
        "members": [user_id],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    docs.append(legacy_channel)
    
    return serialize_doc(docs)

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

    try:
        oid = ObjectId(channel_id)
    except Exception:
        return []
        
    docs = await db["messages"].find({"channel_id": oid, "parent_id": None}).sort("created_at", -1).skip(skip).limit(limit).to_list(None)
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
                    
                    channel = await db["channels"].find_one({"_id": ObjectId(channel_id)})
                    if not channel:
                        continue
                        
                    doc = {
                        "channel_id": ObjectId(channel_id),
                        "course_code": channel.get("course_code"),
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
                    
                    if "members" in channel:
                        for member in channel["members"]:
                            await manager.send_to_user(str(member), broadcast_data)
                    else:
                        await manager.send_to_user(str(user_id), broadcast_data)
                        
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)