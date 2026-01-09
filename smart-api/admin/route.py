from fastapi import Depends, HTTPException, status, Form
from authentication import get_current_user
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy import func
from database import get_db
from models import *
from typing import Optional
# from . import router

from fastapi import APIRouter

router = APIRouter(prefix="/admin", tags=["admin"])

def admin_required(roles: list[str]):
    def guard(user=Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(403, "Admin access required")
        return user
    return guard


@router.patch("/workers/{worker_id}/status")
def admin_update_worker_status(
    worker_id: int,
    status: str = Form(...),  # approved | suspended | rejected
    db: Session = Depends(get_db),
    admin=Depends(admin_required(["operations_admin"]))
):
    worker = db.query(Workers).get(worker_id)
    if not worker:
        raise HTTPException(404, "Worker not found")

    worker.status = status
    db.commit()

    return {"message": f"Worker {status}"}
@router.get("/payments")
def admin_payments(
    worker_id: Optional[int] = None,
    db: Session = Depends(get_db),
    admin=Depends(admin_required(["finance_admin"]))
):
    q = db.query(WorkerPayments)

    if worker_id:
        q = q.filter(WorkerPayments.worker_id == worker_id)

    return q.order_by(WorkerPayments.payment_date.desc()).all()
@router.post("/workers/{worker_id}/payout")
def admin_payout_worker(
    worker_id: int,
    amount: float = Form(...),
    method: str = Form(...),
    db: Session = Depends(get_db),
    admin=Depends(admin_required(["finance_admin"]))
):
    payment = WorkerPayments(
        worker_id=worker_id,
        amount=amount,
        payment_method=method,
        payment_date=datetime.utcnow(),
        work_done="Admin payout"
    )
    db.add(payment)
    db.commit()

    return {"message": "Payout successful"}
@router.get("/dashboard")
def admin_dashboard(
    db: Session = Depends(get_db),
    admin=Depends(admin_required(["admin", "finance_admin"]))
):
    return {
        "total_workers": db.query(func.count(Workers.id)).scalar(),
        "active_workers": db.query(func.count(Workers.id)).filter(Workers.status=="approved").scalar(),
        "total_earnings": db.query(func.coalesce(func.sum(WorkerPayments.amount),0)).scalar(),
        "pending_jobs": db.query(func.count(Booking.id)).filter(Booking.status=="pending").scalar(),
    }
@router.delete("/reviews/{review_id}")
def admin_delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    admin=Depends(admin_required(["admin", "support_admin"]))
):
    review = db.query(WorkerRating).get(review_id)
    if not review:
        raise HTTPException(404)

    db.delete(review)
    db.commit()
    return {"message": "Review removed"}
@router.post("/notifications/broadcast")
def admin_broadcast_notification(
    title: str = Form(...),
    message: str = Form(...),
    db: Session = Depends(get_db),
    admin=Depends(admin_required(["admin"]))
):
    users = db.query(User).all()
    for user in users:
        db.add(Notification(
            user_id=user.id,
            title=title,
            message=message
        ))
    db.commit()

    return {"message": "Broadcast sent"}
@router.patch("/users/{user_id}/role")
def admin_set_role(
    user_id: int,
    role: str = Form(...),
    db: Session = Depends(get_db),
    admin=Depends(admin_required(["super_admin"]))
):
    user = db.query(User).get(user_id)
    user.role = role
    db.commit()
    return {"message": "Role updated"}
