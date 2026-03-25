"""
WebSocket Manager for Real-Time Updates
Handles WebSocket connections and broadcasts
"""

import json
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        # user_id -> set of websocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Connect a WebSocket client"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        print(f"WebSocket connected: user={user_id}, total={len(self.active_connections[user_id])}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Disconnect a WebSocket client"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            
            # Clean up empty sets
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        print(f"WebSocket disconnected: user={user_id}")
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to specific user"""
        if user_id not in self.active_connections:
            return
        
        disconnected = set()
        
        for connection in self.active_connections[user_id]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)
        
        # Clean up disconnected
        for conn in disconnected:
            self.active_connections[user_id].discard(conn)
    
    async def broadcast_event_update(self, user_id: str, event_data: dict, action: str):
        """Broadcast event update to user"""
        message = {
            "type": "event_update",
            "action": action,  # "created", "updated", "deleted"
            "event": event_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.send_personal_message(message, user_id)
    
    async def broadcast_agent_message(self, user_id: str, message: str):
        """Broadcast agent message to user"""
        msg = {
            "type": "agent_message",
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.send_personal_message(msg, user_id)
    
    async def broadcast_error(self, user_id: str, error: str):
        """Broadcast error to user"""
        msg = {
            "type": "error",
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.send_personal_message(msg, user_id)
    
    def get_connection_count(self, user_id: str) -> int:
        """Get number of active connections for user"""
        return len(self.active_connections.get(user_id, set()))
    
    def get_total_connections(self) -> int:
        """Get total number of connections"""
        return sum(len(conns) for conns in self.active_connections.values())


# Global connection manager
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint handler"""
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Keep connection alive, handle incoming messages
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                # Handle incoming messages if needed
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, user_id)


# Helper to broadcast from anywhere in the app
async def notify_event_created(user_id: str, event: dict):
    """Notify about created event"""
    await manager.broadcast_event_update(user_id, event, "created")


async def notify_event_updated(user_id: str, event: dict):
    """Notify about updated event"""
    await manager.broadcast_event_update(user_id, event, "updated")


async def notify_event_deleted(user_id: str, event_id: str):
    """Notify about deleted event"""
    await manager.broadcast_event_update(
        user_id, 
        {"id": event_id}, 
        "deleted"
    )


async def notify_agent_response(user_id: str, message: str):
    """Notify about agent response"""
    await manager.broadcast_agent_message(user_id, message)
