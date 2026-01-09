from . import ConnectionManager
from fastapi import Depends, HTTPException, status,APIRouter
from sqlalchemy.orm import Session
from database import get_db
from models import User, Booking, Message
from schemas import MessageCreate, MessageResponse,MarkReadRequest
from authentication import get_current_user
#from dependencies.auth import get_current_user, get_current_user_ws
from typing import List
from fastapi import WebSocket, WebSocketDisconnect

router = APIRouter(prefix="/messages", tags=["messages"])


manager = ConnectionManager()

@router.post("/", response_model=MessageResponse)
def send_message(
    data: MessageCreate,
    db: Session = Depends(get_db)
):
    # Fetch booking
    booking = db.query(Booking).filter_by(id=data.booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Determine sender and receiver IDs
    if data.sender_type == "client":
        if not booking.client:
            raise HTTPException(status_code=400, detail="Client not found for this booking")
        sender_id = booking.client.user_id
        receiver_id = booking.worker.user_id if booking.worker else None
    elif data.sender_type == "worker":
        if not booking.worker:
            raise HTTPException(status_code=400, detail="Worker not found for this booking")
        sender_id = booking.worker.user_id
        receiver_id = booking.client.user_id
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

    return message

@router.post("/read")
def mark_message_as_read(
    data: MarkReadRequest,
    db: Session = Depends(get_db)
):
    # Fetch the message
    message = db.query(Message).filter_by(id=data.message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Determine the expected reader
    booking = message.booking
    if not booking:
        raise HTTPException(status_code=400, detail="Booking not associated with this message")

    if data.reader_type == "client":
        if not booking.client or message.receiver_id != booking.client.user_id:
            raise HTTPException(status_code=403, detail="This message cannot be read by client")
    elif data.reader_type == "worker":
        if not booking.worker or message.receiver_id != booking.worker.user_id:
            raise HTTPException(status_code=403, detail="This message cannot be read by worker")
    else:
        raise HTTPException(status_code=400, detail="reader_type must be 'client' or 'worker'")

    # Update read status
    message.is_read = True
    db.commit()
    db.refresh(message)

    return {"detail": "Message marked as read", "message_id": message.id}


@router.get("/booking/{booking_id}", response_model=List[MessageResponse])
def get_messages_for_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter_by(id=booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    messages = (
        db.query(Message)
        .filter(Message.booking_id == booking_id)
        .order_by(Message.sent_at.asc())
        .all()
    )

    return messages