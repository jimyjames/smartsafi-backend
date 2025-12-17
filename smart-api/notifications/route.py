# filepath: routes/notifications.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Notification, User, Workers
from schemas import NotificationResponse, NotificationCreate
from typing import List
from datetime import datetime

router = APIRouter(prefix="/notifications", tags=["notifications"])


# ==============================
# Get all notifications for a user
# ==============================
@router.get("/user/{user_id}", response_model=List[NotificationResponse])
def get_user_notifications(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    return notifications


# ==============================
# Create a notification
# ==============================
@router.post("/", response_model=NotificationResponse)
def create_notification(payload: NotificationCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_notification = Notification(
        user_id=payload.user_id,
        message=payload.message,
        type=payload.type,
        is_read=False,
        created_at=datetime.utcnow(),
    )
    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)
    return new_notification


# ==============================
# Mark notification as read
# ==============================
@router.put("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_as_read(notification_id: int, db: Session = Depends(get_db)):
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


# ==============================
# Delete notification
# ==============================
@router.delete("/{notification_id}")
def delete_notification(notification_id: int, db: Session = Depends(get_db)):
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    db.delete(notification)
    db.commit()
    return {"detail": "Notification deleted successfully"}


def get_worker_notifications(worker_id: int, db: Session = Depends(get_db)):
    worker = db.query(Workers).filter(Workers.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    notifications = db.query(Notification).filter(Notification.user_id == worker.user_id, Notification.is_read == False).all()
    return notifications