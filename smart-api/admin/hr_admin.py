# hr/router.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from sqlalchemy import func, desc
from datetime import datetime, timedelta

from database import get_db
from models import Workers, WorkerRating, WorkerPayments, Booking, User
from authentication import require_hr, require_staff
from schemas import (
    WorkerPerformanceResponse,
    HRDashboardStats,
    PayrollSummary,
    WorkerVerificationRequest
)

router = APIRouter(prefix="/hr", tags=["hr"])

# ==========================
# HR DASHBOARD
# ==========================
@router.get("/dashboard", response_model=HRDashboardStats)
def get_hr_dashboard(
    current_user: User = Depends(require_hr),
    db: Session = Depends(get_db)
):
    """HR dashboard with worker statistics"""
    
    total_workers = db.query(Workers).count()
    active_workers = db.query(Workers).filter(Workers.verification_id == True).count()
    pending_verification = db.query(Workers).filter(Workers.verification_id == False).count()
    
    # Recent registrations (last 7 days)
    recent_registrations = db.query(Workers).options(
        joinedload(Workers.user)
    ).filter(
        Workers.user.has(User.created_at >= datetime.utcnow() - timedelta(days=7))
    ).order_by(desc(Workers.id)).limit(10).all()
    
    # Top performers by rating
    top_performers = db.query(Workers).filter(
        Workers.average_rating >= 4.0,
        Workers.jobs_completed >= 5
    ).order_by(desc(Workers.average_rating)).limit(5).all()
    
    # Workers needing attention (low ratings)
    low_performers = db.query(Workers).filter(
        Workers.average_rating < 3.0,
        Workers.jobs_completed >= 3
    ).order_by(Workers.average_rating).limit(5).all()
    
    return {
        "total_workers": total_workers,
        "active_workers": active_workers,
        "pending_verification": pending_verification,
        "recent_registrations": recent_registrations,
        "top_performers": top_performers,
        "low_performers": low_performers
    }

# ==========================
# WORKER VERIFICATION
# ==========================
@router.get("/workers/verification-requests")
def get_verification_requests(
    current_user: User = Depends(require_hr),
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None, regex="^(pending|approved|rejected)$")
):
    """Get worker verification requests"""
    
    query = db.query(Workers).options(
        joinedload(Workers.user)
    ).filter(
        Workers.verification_id == False
    )
    
    if status == "pending":
        query = query.filter(Workers.verification_id == False)
    # Add more status filters as needed
    
    workers = query.order_by(Workers.id.desc()).all()
    
    return workers

@router.post("/workers/{worker_id}/verify")
def verify_worker(
    worker_id: int,
    verification_data: WorkerVerificationRequest,
    current_user: User = Depends(require_hr),
    db: Session = Depends(get_db)
):
    """HR verifies a worker"""
    
    worker = db.query(Workers).filter(Workers.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    # Update verification status
    if verification_data.approve:
        worker.verification_id = True
        if verification_data.verify_good_conduct:
            worker.verification_good_conduct = True
        if verification_data.verify_company_reg:
            worker.verification_company_registration = True
        
        # Create notification for worker
        notification = Notification(
            user_id=worker.user_id,
            title="Account Verified",
            message="Your account has been verified by HR. You can now accept bookings.",
            is_read=False
        )
        db.add(notification)
        
        message = "Worker verified successfully"
    else:
        # Reject with reason
        notification = Notification(
            user_id=worker.user_id,
            title="Verification Rejected",
            message=f"Your verification was rejected. Reason: {verification_data.rejection_reason}",
            is_read=False
        )
        db.add(notification)
        message = "Worker verification rejected"
    
    db.commit()
    
    return {"message": message}

# ==========================
# WORKER PERFORMANCE
# ==========================
@router.get("/workers/performance", response_model=List[WorkerPerformanceResponse])
def get_worker_performance(
    current_user: User = Depends(require_hr),
    db: Session = Depends(get_db),
    min_jobs: int = Query(1, ge=1),
    min_rating: float = Query(0.0, ge=0.0, le=5.0)
):
    """Get worker performance metrics"""
    
    workers = db.query(Workers).options(
        joinedload(Workers.ratings),
        joinedload(Workers.user)
    ).filter(
        Workers.jobs_completed >= min_jobs,
        Workers.average_rating >= min_rating
    ).all()
    
    performance_data = []
    
    for worker in workers:
        # Calculate completion rate
        total_assigned = db.query(Booking).filter(
            Booking.worker_id == worker.id
        ).count()
        
        completion_rate = (worker.jobs_completed / total_assigned * 100) if total_assigned > 0 else 0
        
        # Get recent ratings (last 5)
        recent_ratings = db.query(WorkerRating).filter(
            WorkerRating.worker_id == worker.id
        ).order_by(WorkerRating.created_at.desc()).limit(5).all()
        
        # Calculate response time (average time to accept bookings)
        # This would require additional fields in Booking model
        
        performance_data.append({
            "worker_id": worker.id,
            "name": f"{worker.first_name} {worker.last_name}",
            "email": worker.user.email,
            "phone": worker.phone_number,
            "average_rating": worker.average_rating,
            "jobs_completed": worker.jobs_completed,
            "completion_rate": round(completion_rate, 2),
            "verification_status": worker.verification_id,
            "recent_ratings": recent_ratings
        })
    
    return performance_data

# ==========================
# PAYROLL MANAGEMENT
# ==========================
@router.get("/payroll/summary", response_model=List[PayrollSummary])
def get_payroll_summary(
    current_user: User = Depends(require_hr),
    db: Session = Depends(get_db),
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2020)
):
    """Get payroll summary"""
    
    query = db.query(WorkerPayments).options(
        joinedload(WorkerPayments.worker).joinedload(Workers.user)
    )
    
    if month and year:
        query = query.filter(
            func.extract('month', WorkerPayments.payment_date) == month,
            func.extract('year', WorkerPayments.payment_date) == year
        )
    
    payments = query.all()
    
    # Group by worker
    payroll_summary = {}
    for payment in payments:
        worker_id = payment.worker_id
        if worker_id not in payroll_summary:
            worker = payment.worker
            payroll_summary[worker_id] = {
                "worker_id": worker_id,
                "worker_name": f"{worker.first_name} {worker.last_name}",
                "total_amount": 0,
                "payment_count": 0,
                "payments": []
            }
        
        payroll_summary[worker_id]["total_amount"] += payment.amount
        payroll_summary[worker_id]["payment_count"] += 1
        payroll_summary[worker_id]["payments"].append(payment)
    
    return list(payroll_summary.values())

@router.get("/payroll/{worker_id}")
def get_worker_payroll(
    worker_id: int,
    current_user: User = Depends(require_hr),
    db: Session = Depends(get_db),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Get detailed payroll for a specific worker"""
    
    worker = db.query(Workers).filter(Workers.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    query = db.query(WorkerPayments).filter(WorkerPayments.worker_id == worker_id)
    
    if start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(WorkerPayments.payment_date >= start)
    
    if end_date:
        end = datetime.strptime(end_date, "%Y-%m-%d")
        query = query.filter(WorkerPayments.payment_date <= end)
    
    payments = query.order_by(WorkerPayments.payment_date.desc()).all()
    
    total_amount = sum(p.amount for p in payments)
    
    return {
        "worker": {
            "id": worker.id,
            "name": f"{worker.first_name} {worker.last_name}",
            "mpesa_number": worker.mpesa_number,
            "bank_details": {
                "bank_name": worker.bank_name,
                "account_name": worker.bank_account_name,
                "account_number": worker.bank_account_number
            }
        },
        "payments": payments,
        "summary": {
            "total_payments": len(payments),
            "total_amount": float(total_amount),
            "average_payment": float(total_amount / len(payments)) if payments else 0
        }
    }

# ==========================
# WORKER DETAILS (HR VIEW)
# ==========================
@router.get("/workers/{worker_id}")
def get_worker_full_details(
    worker_id: int,
    current_user: User = Depends(require_hr),
    db: Session = Depends(get_db)
):
    """HR can view complete worker details"""
    
    worker = db.query(Workers).options(
        joinedload(Workers.user),
        joinedload(Workers.emergency_contacts),
        joinedload(Workers.equipments),
        joinedload(Workers.services),
        joinedload(Workers.ratings),
        joinedload(Workers.languages).joinedload(WorkerLanguages.language)
    ).filter(Workers.id == worker_id).first()
    
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    # Get additional data
    payments = db.query(WorkerPayments).filter(
        WorkerPayments.worker_id == worker_id
    ).order_by(WorkerPayments.payment_date.desc()).limit(20).all()
    
    bookings = db.query(Booking).filter(
        Booking.worker_id == worker_id
    ).order_by(Booking.date_of_booking.desc()).limit(20).all()
    
    total_earnings = sum(p.amount for p in payments)
    
    return {
        "worker": worker,
        "financial_summary": {
            "total_earnings": float(total_earnings),
            "total_payments": len(payments),
            "pending_earnings": 0,  # Calculate based on pending bookings
            "average_rating": worker.average_rating,
            "jobs_completed": worker.jobs_completed
        },
        "recent_payments": payments,
        "recent_bookings": bookings
    }