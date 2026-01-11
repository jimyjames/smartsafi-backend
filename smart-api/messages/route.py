from . import ConnectionManager
from fastapi import Depends, HTTPException, status, APIRouter, Query
from sqlalchemy.orm import Session
from database import get_db
from datetime import datetime
from models import User, Booking, Message
from schemas import MessageCreate, MessageResponse, MarkReadRequest, ConversationResponse, MessageItem, UserSummary
from typing import List
from fastapi import WebSocket, WebSocketDisconnect
import json

# Import FCM Service
from .fcm import FCMService

router = APIRouter(prefix="/messages", tags=["messages"])
manager = ConnectionManager()

@router.post("/send", response_model=MessageResponse)
async def send_message(  # Change to async function
    data: MessageCreate,
    db: Session = Depends(get_db)
):
    # Verify user exists
    current_user = db.query(User).filter_by(id=data.user_id).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Fetch booking
    booking = db.query(Booking).filter_by(id=data.booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Determine sender and receiver IDs based on sender_type
    if data.sender_type == "client":
        if not booking.client:
            raise HTTPException(status_code=400, detail="Client not found for this booking")
        if booking.client.user_id != data.user_id:
            raise HTTPException(status_code=403, detail="Not authorized as client")
        sender_id = booking.client.user_id
        receiver_id = booking.worker.user_id if booking.worker else None
        sender_name = f"{booking.client.first_name} {booking.client.last_name}"
    elif data.sender_type == "worker":
        if not booking.worker:
            raise HTTPException(status_code=400, detail="Worker not found for this booking")
        if booking.worker.user_id != data.user_id:
            raise HTTPException(status_code=403, detail="Not authorized as worker")
        sender_id = booking.worker.user_id
        receiver_id = booking.client.user_id
        sender_name = f"{booking.worker.first_name} {booking.worker.last_name}"
    else:
        raise HTTPException(status_code=400, detail="sender_type must be 'client' or 'worker'")

    if receiver_id is None:
        raise HTTPException(status_code=400, detail="Receiver not found")

    # Create message
    message = Message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        booking_id=data.booking_id,
        content=data.content
    )

    db.add(message)
    db.commit()
    db.refresh(message)
    
    # Get receiver details
    receiver = db.get(User, receiver_id)
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver user not found")
    
    # Prepare WebSocket message
    ws_message = {
        "type": "new_message",
        "message_id": message.id,
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "sender_type": data.sender_type,
        "content": data.content,
        "timestamp": message.sent_at.isoformat(),
        "booking_id": booking.id,
        "sender_name": sender_name
    }
    
    # Try to send via WebSocket first
    is_online = manager.is_user_online(booking.id, receiver_id)
    
    if is_online:
        # User is online, send via WebSocket
        sent = await manager.send_to_user(booking.id, receiver_id, ws_message)  # Now this is okay in async function
        if sent:
            print(f"Message sent via WebSocket to user {receiver_id}")
        else:
            is_online = False  # Fallback to FCM if WebSocket fails
    else:
        print(f"User {receiver_id} is offline")
    
    # Send push notification if receiver is offline or WebSocket failed
    if not is_online and receiver.fcm_token:
        print(f"Sending FCM notification to user {receiver_id}")
        
        # Prepare notification data
        notification_data = {
            "type": "new_message",
            "message_id": str(message.id),
            "booking_id": str(booking.id),
            "sender_id": str(sender_id),
            "sender_type": data.sender_type,
            "sender_name": sender_name,
            "content": data.content[:100],  # Truncate for notification
            "timestamp": message.sent_at.isoformat()
        }
        
        # Send push notification
        success = FCMService.send_message_notification(
            fcm_token=receiver.fcm_token,
            title=f"New message from {sender_name}",
            body=data.content[:100],
            data=notification_data
        )
        
        if success:
            print(f"FCM notification sent successfully to user {receiver_id}")
        else:
            print(f"Failed to send FCM notification to user {receiver_id}")
    
    # Also broadcast to all connected clients in this booking (for real-time updates)
    await manager.broadcast(booking.id, ws_message, exclude_user_id=sender_id)
    
    return message

@router.post("/read")
async def mark_message_as_read(  # Change to async function
    data: MarkReadRequest,
    db: Session = Depends(get_db),
    user_id: int = Query(..., description="User ID for authentication")
):
    # Fetch the message
    message = db.query(Message).filter_by(id=data.message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Determine the expected reader
    booking = message.booking
    if not booking:
        raise HTTPException(status_code=400, detail="Booking not associated with this message")

    # Verify user is authorized to mark as read
    if data.reader_type == "client":
        if not booking.client or booking.client.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized as client")
    elif data.reader_type == "worker":
        if not booking.worker or booking.worker.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized as worker")
    else:
        raise HTTPException(status_code=400, detail="reader_type must be 'client' or 'worker'")

    # Update read status
    message.is_read = True
    message.read_at = datetime.utcnow()
    db.commit()
    db.refresh(message)
    
    # Broadcast read receipt via WebSocket
    ws_message = {
        "type": "message_read",
        "message_id": message.id,
        "user_id": user_id,
        "timestamp": message.read_at.isoformat(),
        "booking_id": booking.id
    }
    
    await manager.broadcast(booking.id, ws_message, exclude_user_id=user_id)

    return {"detail": "Message marked as read", "message_id": message.id}

# Helper to format time
def format_time(dt: datetime) -> str:
    now = datetime.utcnow()
    diff = now - dt
    seconds = diff.total_seconds()
    if seconds < 60:
        return f"{int(seconds)} sec ago"
    elif seconds < 3600:
        return f"{int(seconds // 60)} min ago"
    elif seconds < 86400:
        return f"{int(seconds // 3600)} hr ago"
    else:
        return dt.strftime("%b %d, %Y %I:%M %p")

# Endpoint to fetch conversation by booking
@router.get("/booking/{booking_id}", response_model=ConversationResponse)
def get_booking_conversation(  # This can stay synchronous
    booking_id: int,
    db: Session = Depends(get_db),
    user_id: int = Query(..., description="User ID for authentication")
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Verify user has access to this booking
    user_has_access = (
        (booking.client and booking.client.user_id == user_id) or
        (booking.worker and booking.worker.user_id == user_id)
    )
    if not user_has_access:
        raise HTTPException(status_code=403, detail="Not authorized to access this booking")

    provider = booking.worker
    client = booking.client
    if not provider or not client:
        raise HTTPException(status_code=404, detail="Client or provider not assigned")

    provider_user = provider.user
    client_user = client.user

    messages = db.query(Message).filter(Message.booking_id == booking_id).order_by(Message.sent_at.asc()).all()
    
    unread_count = 0
    messages_list = []

    for m in messages:
        sender_role = "provider" if m.sender_id == provider_user.id else "client"
        if not m.is_read and m.receiver_id == user_id:
            unread_count += 1
        messages_list.append(
            MessageItem(
                id=m.id,
                sender=sender_role,
                text=m.content,
                timestamp=m.sent_at.strftime("%I:%M %p"),
                read=m.is_read,
                delivered=m.delivered_at is not None
            )
        )

    last_message = messages[-1].content if messages else None
    last_timestamp = format_time(messages[-1].sent_at) if messages else None

    # Check online status via WebSocket manager
    client_online = manager.is_user_online(booking_id, client_user.id)
    provider_online = manager.is_user_online(booking_id, provider_user.id)

    client_summary = UserSummary(
        name=f"{client.first_name} {client.last_name}",
        profilePicture=client.profile_picture,
        rating=None,
        status="online" if client_online else "offline"
    )
    provider_summary = UserSummary(
        name=f"{provider.first_name} {provider.last_name}",
        profilePicture=provider.profile_picture,
        rating=None,
        status="online" if provider_online else "offline"
    )

    return ConversationResponse(
        bookingId=booking.id,
        client=client_summary,
        provider=provider_summary,
        lastMessage=last_message,
        timestamp=last_timestamp,
        unread=unread_count,
        messages=messages_list
    )

@router.websocket("/ws/chat/{booking_id}/{user_id}")
async def chat_ws(
    websocket: WebSocket,
    booking_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    # Verify user exists
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        await websocket.close(code=1008)
        return
    
    # Verify booking exists
    booking = db.query(Booking).filter_by(id=booking_id).first()
    if not booking:
        await websocket.close(code=1008)
        return
    
    # Verify user has access to this booking
    if not ((booking.client and booking.client.user_id == user_id) or 
            (booking.worker and booking.worker.user_id == user_id)):
        await websocket.close(code=1008)
        return
    
    # Connect to chat
    await manager.connect(booking_id, user_id, websocket)
    
    # Update user online status in database
    user.is_online = True
    user.last_seen = None
    db.commit()

    try:
        while True:
            data = await websocket.receive_json()
            
            if data["type"] == "typing":
                # Broadcast typing indicator
                is_typing = data.get("is_typing", False)
                await manager.send_typing_indicator(booking_id, user_id, is_typing)
            
            elif data["type"] == "message_delivered":
                # Mark message as delivered
                message_id = data.get("message_id")
                if message_id:
                    message = db.query(Message).filter_by(id=message_id).first()
                    if message and message.receiver_id == user_id:
                        message.delivered_at = datetime.utcnow()
                        db.commit()
                        # Broadcast delivery receipt
                        await manager.broadcast(
                            booking_id,
                            {
                                "type": "message_delivered",
                                "message_id": message_id,
                                "user_id": user_id,
                                "timestamp": datetime.utcnow().isoformat()
                            },
                            exclude_user_id=user_id
                        )
            
            elif data["type"] == "ping":
                # Keep connection alive
                await websocket.send_json({"type": "pong"})
            
            elif data["type"] == "new_message":
                # Handle new message sent via WebSocket
                content = data.get("content", "")
                if content:
                    # Determine receiver
                    if user_id == booking.client.user_id:
                        receiver_id = booking.worker.user_id
                        sender_type = "client"
                    else:
                        receiver_id = booking.client.user_id
                        sender_type = "worker"
                    
                    # Create message in database
                    message = Message(
                        sender_id=user_id,
                        receiver_id=receiver_id,
                        booking_id=booking_id,
                        content=content
                    )
                    db.add(message)
                    db.commit()
                    db.refresh(message)
                    
                    # Broadcast to all connected clients
                    await manager.broadcast(
                        booking_id,
                        {
                            "type": "new_message",
                            "message_id": message.id,
                            "sender_id": user_id,
                            "receiver_id": receiver_id,
                            "sender_type": sender_type,
                            "content": content,
                            "timestamp": message.sent_at.isoformat()
                        },
                        exclude_user_id=user_id
                    )

    except WebSocketDisconnect:
        # Handle disconnect
        await manager.disconnect(booking_id, user_id, websocket)
        user.is_online = False
        user.last_seen = datetime.utcnow()
        db.commit()
    except Exception as e:
        print(f"WebSocket error: {e}")
        await manager.disconnect(booking_id, user_id, websocket)
        user.is_online = False
        user.last_seen = datetime.utcnow()
        db.commit()

@router.get("/online_status/{booking_id}")
async def get_online_status(  # Change to async function
    booking_id: int,
    user_id: int = Query(..., description="User ID for authentication"),
    db: Session = Depends(get_db)
):
    """Get online status of participants in a booking"""
    booking = db.query(Booking).filter_by(id=booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Get online users via WebSocket manager
    online_user_ids = manager.get_online_users(booking_id)
    
    participants = []
    
    if booking.client:
        client_user = booking.client.user
        participants.append({
            "user_id": client_user.id,
            "role": "client",
            "name": f"{booking.client.first_name} {booking.client.last_name}",
            "is_online": client_user.id in online_user_ids,
            "last_seen": client_user.last_seen.isoformat() if client_user.last_seen else None
        })
    
    if booking.worker:
        worker_user = booking.worker.user
        participants.append({
            "user_id": worker_user.id,
            "role": "worker",
            "name": f"{booking.worker.first_name} {booking.worker.last_name}",
            "is_online": worker_user.id in online_user_ids,
            "last_seen": worker_user.last_seen.isoformat() if worker_user.last_seen else None
        })
    
    return {"participants": participants}