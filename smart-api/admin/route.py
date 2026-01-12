# admin/router.py
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from sqlalchemy import func, or_, and_
from datetime import datetime, timedelta

from database import get_db
from models import User, Client, Workers, Booking, Payment, Notification, AdminProfile
from authentication import require_admin,require_staff,get_current_user
from schemas import (
    AdminDashboardStats,
    UserManagementResponse,
    BookingAnalytics,
    AdminProfileCreate,
    AdminProfileResponse
)

router = APIRouter(prefix="/admin", tags=["admin"])

# ==========================
# ADMIN DASHBOARD
# ==========================
@router.get("/dashboard", response_model=AdminDashboardStats)
def get_admin_dashboard(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get comprehensive admin dashboard statistics"""
    
    # User statistics
    total_users = db.query(User).count()
    users_today = db.query(User).filter(
        func.date(User.created_at) == datetime.utcnow().date()
    ).count()
    
    users_by_role = db.query(
        User.role,
        func.count(User.id).label("count")
    ).group_by(User.role).all()
    
    # Client statistics
    total_clients = db.query(Client).count()
    verified_clients = db.query(Client).filter(Client.verification_id == True).count()
    
    # Worker statistics
    total_workers = db.query(Workers).count()
    verified_workers = db.query(Workers).filter(Workers.verification_id == True).count()
    pending_verification = db.query(Workers).filter(
        Workers.verification_id == False
    ).count()
    
    # Booking statistics
    total_bookings = db.query(Booking).count()
    bookings_today = db.query(Booking).filter(
        func.date(Booking.date_of_booking) == datetime.utcnow().date()
    ).count()
    pending_bookings = db.query(Booking).filter(Booking.status == "pending").count()
    completed_bookings = db.query(Booking).filter(Booking.status == "completed").count()
    
    # Financial statistics
    total_revenue = db.query(func.sum(Payment.amount)).filter(
        Payment.status == "succeeded"
    ).scalar() or 0
    
    revenue_today = db.query(func.sum(Payment.amount)).filter(
        Payment.status == "succeeded",
        func.date(Payment.created_at) == datetime.utcnow().date()
    ).scalar() or 0
    
    # Recent activity
    recent_users = db.query(User).order_by(User.created_at.desc()).limit(5).all()
    recent_bookings = db.query(Booking).order_by(Booking.date_of_booking.desc()).limit(5).all()
    
    return {
        "total_users": total_users,
        "users_today": users_today,
        "users_by_role": dict(users_by_role),
        "total_clients": total_clients,
        "verified_clients": verified_clients,
        "total_workers": total_workers,
        "verified_workers": verified_workers,
        "pending_verification": pending_verification,
        "total_bookings": total_bookings,
        "bookings_today": bookings_today,
        "pending_bookings": pending_bookings,
        "completed_bookings": completed_bookings,
        "total_revenue": float(total_revenue),
        "revenue_today": float(revenue_today),
        "recent_users": recent_users,
        "recent_bookings": recent_bookings
    }

# ==========================
# USER MANAGEMENT
# ==========================
@router.get("/users", response_model=List[UserManagementResponse])
def get_all_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    role: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    verified: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get all users with filtering and pagination"""
    
    query = db.query(User)
    
    # Apply filters
    if role:
        query = query.filter(User.role == role)
    
    if search:
        query = query.filter(
            or_(
                User.email.ilike(f"%{search}%"),
                User.public_user_id.ilike(f"%{search}%")
            )
        )
    
    if verified is not None:
        query = query.filter(User.is_verified == verified)
    
    # Pagination
    offset = (page - 1) * limit
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "users": users,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }

@router.get("/users/{user_id}")
def get_user_details(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get detailed user information"""
    
    user = db.query(User).options(
        joinedload(User.client),
        joinedload(User.worker),
        joinedload(User.notifications)
    ).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user bookings based on role
    bookings = []
    if user.role == "client":
        bookings = db.query(Booking).filter(Booking.client_id == user.client.id).all()
    elif user.role == "worker":
        bookings = db.query(Booking).filter(Booking.worker_id == user.worker.id).all()
    
    return {
        "user": user,
        "bookings": bookings
    }

@router.put("/users/{user_id}/verify")
def verify_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin verifies a user"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_verified = True
    db.commit()
    
    return {"message": "User verified successfully"}

@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    role: str = Form(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update user role (admin only)"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate role
    valid_roles = ["client", "worker", "admin", "hr", "manager", "support", "finance"]
    if role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}")
    
    user.role = role
    user.is_admin = (role == "admin")
    
    # Create admin profile if needed
    if role == "admin":
        existing_profile = db.query(AdminProfile).filter(AdminProfile.user_id == user_id).first()
        if not existing_profile:
            admin_profile = AdminProfile(user_id=user_id)
            db.add(admin_profile)
    
    db.commit()
    
    return {"message": "User role updated successfully"}

# ==========================
# WORKER MANAGEMENT (ADMIN)
# ==========================
@router.get("/workers/pending-verification")
def get_pending_worker_verifications(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get workers pending verification"""
    
    pending_workers = db.query(Workers).options(
        joinedload(Workers.user)
    ).filter(
        Workers.verification_id == False
    ).all()
    
    return pending_workers

@router.post("/workers/{worker_id}/verify-id")
def verify_worker_id(
    worker_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin verifies worker ID"""
    
    worker = db.query(Workers).filter(Workers.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    worker.verification_id = True
    db.commit()
    
    return {"message": "Worker ID verified successfully"}

@router.post("/workers/{worker_id}/verify-documents")
def verify_worker_documents(
    worker_id: int,
    verify_good_conduct: bool = Form(False),
    verify_company_reg: bool = Form(False),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin verifies worker documents"""
    
    worker = db.query(Workers).filter(Workers.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    if verify_good_conduct:
        worker.verification_good_conduct = True
    
    if verify_company_reg:
        worker.verification_company_registration = True
    
    db.commit()
    
    return {"message": "Worker documents verified successfully"}

# ==========================
# BOOKING MANAGEMENT (ADMIN)
# ==========================
@router.get("/bookings")
def get_all_bookings(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get all bookings with filtering"""
    
    query = db.query(Booking).options(
        joinedload(Booking.client),
        joinedload(Booking.worker),
        joinedload(Booking.feature)
    )
    
    # Apply filters
    if status:
        query = query.filter(Booking.status == status)
    
    if start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(Booking.date_of_booking >= start)
    
    if end_date:
        end = datetime.strptime(end_date, "%Y-%m-%d")
        query = query.filter(Booking.date_of_booking <= end)
    
    # Pagination
    offset = (page - 1) * limit
    total = query.count()
    bookings = query.order_by(Booking.date_of_booking.desc()).offset(offset).limit(limit).all()
    
    return {
        "bookings": bookings,
        "total": total,
        "page": page,
        "limit": limit
    }

@router.put("/bookings/{booking_id}/assign-worker")
def assign_worker_to_booking(
    booking_id: int,
    worker_id: int = Form(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin assigns a worker to a booking"""
    
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    worker = db.query(Workers).filter(Workers.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    booking.worker_id = worker_id
    booking.status = "assigned"
    db.commit()
    
    # Create notification for worker
    notification = Notification(
        user_id=worker.user_id,
        title="New Booking Assigned",
        message=f"You have been assigned to booking {booking.public_id}",
        booking_id=booking_id
    )
    db.add(notification)
    db.commit()
    
    return {"message": "Worker assigned successfully"}

# ==========================
# PAYMENT MANAGEMENT (ADMIN)
# ==========================
@router.get("/payments")
def get_all_payments(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Get all payments"""
    
    query = db.query(Payment).options(
        joinedload(Payment.booking).joinedload(Booking.client),
        joinedload(Payment.booking).joinedload(Booking.worker)
    )
    
    if status:
        query = query.filter(Payment.status == status)
    
    if start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(Payment.created_at >= start)
    
    if end_date:
        end = datetime.strptime(end_date, "%Y-%m-%d")
        query = query.filter(Payment.created_at <= end)
    
    payments = query.order_by(Payment.created_at.desc()).all()
    
    # Summary stats
    total_amount = sum(p.amount for p in payments)
    succeeded_payments = [p for p in payments if p.status == "succeeded"]
    succeeded_amount = sum(p.amount for p in succeeded_payments)
    
    return {
        "payments": payments,
        "summary": {
            "total_payments": len(payments),
            "total_amount": float(total_amount),
            "succeeded_payments": len(succeeded_payments),
            "succeeded_amount": float(succeeded_amount)
        }
    }

# ==========================
# ADMIN PROFILE MANAGEMENT
# ==========================
@router.get("/profile", response_model=AdminProfileResponse)
def get_admin_profile(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get admin profile"""
    
    profile = db.query(AdminProfile).filter(AdminProfile.user_id == current_user.id).first()
    if not profile:
        # Create profile if it doesn't exist
        profile = AdminProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    
    return profile

@router.put("/profile")
def update_admin_profile(
    profile_data: AdminProfileCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update admin profile"""
    
    profile = db.query(AdminProfile).filter(AdminProfile.user_id == current_user.id).first()
    if not profile:
        profile = AdminProfile(user_id=current_user.id, **profile_data.dict())
        db.add(profile)
    else:
        for field, value in profile_data.dict(exclude_unset=True).items():
            setattr(profile, field, value)
    
    db.commit()
    db.refresh(profile)
    
    return {"message": "Profile updated successfully", "profile": profile}

# ==========================
# SYSTEM STATISTICS & ANALYTICS
# ==========================
@router.get("/analytics/bookings")
def get_booking_analytics(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    period: str = Query("monthly", regex="^(daily|weekly|monthly|yearly)$")
):
    """Get booking analytics"""
    
    now = datetime.utcnow()
    
    if period == "daily":
        # Last 30 days
        dates = [(now - timedelta(days=i)).date() for i in range(30)]
        date_format = "%Y-%m-%d"
        group_by = func.date(Booking.date_of_booking)
    elif period == "weekly":
        # Last 12 weeks
        dates = [(now - timedelta(weeks=i)).date() for i in range(12)]
        date_format = "Week %U"
        group_by = func.date_trunc('week', Booking.date_of_booking)
    elif period == "monthly":
        # Last 12 months
        dates = [(now.replace(day=1) - timedelta(days=30*i)).date() for i in range(12)]
        date_format = "%Y-%m"
        group_by = func.date_trunc('month', Booking.date_of_booking)
    else:  # yearly
        # Last 5 years
        dates = [(now.replace(month=1, day=1) - timedelta(days=365*i)).date() for i in range(5)]
        date_format = "%Y"
        group_by = func.date_trunc('year', Booking.date_of_booking)
    
    # Get booking counts
    bookings_by_period = db.query(
        group_by.label("period"),
        func.count(Booking.id).label("count"),
        func.sum(Booking.total_price).label("revenue")
    ).group_by(group_by).order_by(group_by).all()
    
    # Get status distribution
    status_distribution = db.query(
        Booking.status,
        func.count(Booking.id).label("count")
    ).group_by(Booking.status).all()
    
    return {
        "bookings_by_period": [
            {
                "period": str(period),
                "count": count,
                "revenue": float(revenue or 0)
            }
            for period, count, revenue in bookings_by_period
        ],
        "status_distribution": dict(status_distribution)
    }