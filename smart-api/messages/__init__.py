from fastapi import APIRouter, WebSocket
from typing import Dict, List, Optional
import json
from datetime import datetime

router = APIRouter(prefix="/messages", tags=["messages"])

class ConnectionManager:
    def __init__(self):
        # Structure: {booking_id: {user_id: websocket}}
        self.active_connections: Dict[int, Dict[int, WebSocket]] = {}
        # User online status tracking
        self.user_status: Dict[int, Dict[int, bool]] = {}  # {user_id: {booking_id: is_online}}
    
    async def connect(self, booking_id: int, user_id: int, websocket: WebSocket):
        """Connect user to a booking's chat"""
        await websocket.accept()
        
        # Initialize structures if needed
        if booking_id not in self.active_connections:
            self.active_connections[booking_id] = {}
        
        if user_id not in self.user_status:
            self.user_status[user_id] = {}
        
        # Store connection
        self.active_connections[booking_id][user_id] = websocket
        self.user_status[user_id][booking_id] = True
        
        # Notify others in this booking that user came online
        await self.broadcast_user_status(booking_id, user_id, True)
        
        # Send current online users to the newly connected user
        online_users = self.get_online_users(booking_id)
        await websocket.send_json({
            "type": "online_users",
            "users": online_users,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        print(f"User {user_id} connected to booking {booking_id}")
    
    async def disconnect(self, booking_id: int, user_id: int, websocket: WebSocket):
        """Disconnect user from chat"""
        if booking_id in self.active_connections:
            if user_id in self.active_connections[booking_id]:
                del self.active_connections[booking_id][user_id]
        
        if user_id in self.user_status:
            if booking_id in self.user_status[user_id]:
                self.user_status[user_id][booking_id] = False
        
        # Notify others that user went offline
        await self.broadcast_user_status(booking_id, user_id, False)
        
        print(f"User {user_id} disconnected from booking {booking_id}")
    
    async def broadcast(self, booking_id: int, message: dict, exclude_user_id: Optional[int] = None):
        """Broadcast message to all users in a booking"""
        if booking_id not in self.active_connections:
            return
        
        for user_id, websocket in self.active_connections[booking_id].items():
            if user_id == exclude_user_id:
                continue
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"Error sending to user {user_id}: {e}")
    
    async def send_to_user(self, booking_id: int, user_id: int, message: dict):
        """Send message to specific user in a booking"""
        if (booking_id in self.active_connections and 
            user_id in self.active_connections[booking_id]):
            try:
                await self.active_connections[booking_id][user_id].send_json(message)
                return True
            except Exception as e:
                print(f"Error sending to user {user_id}: {e}")
        return False
    
    async def broadcast_user_status(self, booking_id: int, user_id: int, is_online: bool):
        """Broadcast user online/offline status to others in booking"""
        await self.broadcast(
            booking_id,
            {
                "type": "user_status",
                "user_id": user_id,
                "is_online": is_online,
                "timestamp": datetime.utcnow().isoformat()
            },
            exclude_user_id=user_id
        )
    
    def is_user_online(self, booking_id: int, user_id: int) -> bool:
        """Check if user is online in specific booking"""
        return (user_id in self.user_status and 
                booking_id in self.user_status[user_id] and 
                self.user_status[user_id][booking_id])
    
    def get_online_users(self, booking_id: int) -> List[int]:
        """Get list of online user IDs for a booking"""
        if booking_id not in self.active_connections:
            return []
        return list(self.active_connections[booking_id].keys())
    
    async def send_typing_indicator(self, booking_id: int, user_id: int, is_typing: bool):
        """Send typing indicator to other users in booking"""
        await self.broadcast(
            booking_id,
            {
                "type": "typing",
                "user_id": user_id,
                "is_typing": is_typing,
                "timestamp": datetime.utcnow().isoformat()
            },
            exclude_user_id=user_id
        )

manager = ConnectionManager()