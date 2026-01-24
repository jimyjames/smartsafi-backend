# admin/router.py
import os
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from sqlalchemy import func, or_, and_
from uuid import uuid4
from pathlib import Path
import shutil
from datetime import datetime, timedelta

from database import get_db
from models import User, Client, Workers, Booking, Payment, Notification, AdminProfile, AdminPayment
from authentication import create_access_token, require_admin,require_staff,get_current_user,get_password_hash
from schemas import (
    AdminDashboardStats,
    PaginatedUsersResponse,
    UserManagementResponse,
    BookingAnalytics,
    AdminProfileCreate,
    AdminProfileResponse,
    AdminRegister,
    Token,
    AdminProfileComplete
    
)


router = APIRouter(prefix="/admin", tags=["admin"])

### existing admin creating new admin user ####
@router.post("/register/admin", response_model=Token)
def register_admin(
    admin_data: AdminRegister,
    # current_user: User = Depends(require_admin),  # Only admins can create other admins
    db: Session = Depends(get_db)
):
    """Register a new admin user (only accessible by existing admins)"""
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == admin_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    hashed_pw = get_password_hash(admin_data.password)
    
    new_user = User(
        email=admin_data.email,
        hashed_password=hashed_pw,
        role="admin",
        is_admin=True,
        is_verified=True  # Admin users are auto-verified
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create admin profile
    admin_profile = AdminProfile(
        user_id=new_user.id,
        first_name=admin_data.first_name,
        last_name=admin_data.last_name,
        phone_number=admin_data.phone_number,
        department=admin_data.department,
        permissions={  # Default permissions
            "manage_users": True,
            "manage_workers": True,
            "manage_bookings": True,
            "manage_payments": True,
            "view_reports": True,
            "system_settings": True
        }
    )
    
    db.add(admin_profile)
    db.commit()

        # Create access token
    access_token = create_access_token({"sub": new_user.email, "role": new_user.role})
    return {"access_token": access_token, "token_type": "bearer"}
    


# Upload directory for admin profile pictures
ADMIN_UPLOAD_DIR = Path("uploads/admins")
ADMIN_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def save_admin_file(upload_file: UploadFile, user_id: int, file_type: str) -> str:
    """Save uploaded file for admin"""
    if not upload_file:
        return None
    
    filename = f"{user_id}_{file_type}_{uuid4()}{Path(upload_file.filename).suffix}"
    file_path = ADMIN_UPLOAD_DIR / filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    
    return str(file_path)

# ==========================
# ADMIN PROFILE MANAGEMENT
# ==========================
@router.get("/me", response_model=AdminProfileComplete)
def get_my_admin_profile(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get current admin's full profile"""
    
    profile = db.query(AdminProfile).options(
        joinedload(AdminProfile.user)
    ).filter(AdminProfile.user_id == current_user.id).first()
    
    if not profile:
        raise HTTPException(
            status_code=404, 
            detail="Admin profile not found. Please complete your profile."
        )
    
    return profile

@router.post("/create", response_model=AdminProfileResponse)
def create_admin_profile(
    # Personal Information
    first_name: str = Form(...),
    last_name: str = Form(...),
    phone_number: str = Form(...),
    date_of_birth: Optional[str] = Form(None),
    
    # Address
    address: Optional[str] = Form(None),
    
    
    # Employment Details
    department: str = Form("Administration"),
    salary: Optional[float] = Form(None),
    
    # Bank Details
    bank_name: Optional[str] = Form(None),
    bank_account_name: Optional[str] = Form(None),
    bank_account_number: Optional[str] = Form(None),
    bank_branch: Optional[str] = Form(None),
    mpesa_number: Optional[str] = Form(None),
    
   
    # Profile Picture
    profile_picture: Optional[UploadFile] = File(None),
    
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create or update admin profile (for first-time setup)"""
    
    # Check if profile already exists
    existing_profile = db.query(AdminProfile).filter(
        AdminProfile.user_id == current_user.id
    ).first()
    
    if existing_profile:
        raise HTTPException(
            status_code=400, 
            detail="Profile already exists. Use update endpoint instead."
        )
    
    # Parse date of birth if provided
    dob = None
    if date_of_birth:
        try:
            dob = datetime.strptime(date_of_birth, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Parse employment date if provided
  
    # Save profile picture
    profile_pic_path = None
    if profile_picture:
        profile_pic_path = save_admin_file(profile_picture, current_user.id, "profile")
    
    # Create admin profile
    admin_profile = AdminProfile(
        user_id=current_user.id,
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        date_of_birth=dob,
        profile_picture=profile_pic_path,
        address=address,
        department=department,
        salary=salary,
        bank_name=bank_name,
        bank_account_name=bank_account_name,
        bank_account_number=bank_account_number,
        bank_branch=bank_branch,
        mpesa_number=mpesa_number,
        permissions={  # Default permissions for new admin
            "manage_users": True,
            "manage_workers": True,
            "manage_bookings": True,
            "manage_payments": True,
            "view_reports": True,
            "system_settings": False  # Only super admins get this
        }
    )
    
    db.add(admin_profile)
    db.commit()
    db.refresh(admin_profile)
    
    return admin_profile

@router.put("/update", response_model=AdminProfileResponse)
def update_admin_profile(
    # Personal Information
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    date_of_birth: Optional[str] = Form(None),
    
    # Address
    address: Optional[str] = Form(None),
    
    
    # Employment Details
    department: Optional[str] = Form(None),
    salary: Optional[float] = Form(None),
    
    # Bank Details
    bank_name: Optional[str] = Form(None),
    bank_account_name: Optional[str] = Form(None),
    bank_account_number: Optional[str] = Form(None),
    bank_branch: Optional[str] = Form(None),
    mpesa_number: Optional[str] = Form(None),
    
 
    # Profile Picture
    profile_picture: Optional[UploadFile] = File(None),
    
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update admin profile"""
    
    profile = db.query(AdminProfile).filter(AdminProfile.user_id == current_user.id).first()
    
    if not profile:
        raise HTTPException(
            status_code=404, 
            detail="Profile not found. Please create your profile first."
        )
    
    # Update fields if provided
    if first_name:
        profile.first_name = first_name
    if last_name:
        profile.last_name = last_name
    if phone_number:
        profile.phone_number = phone_number
    
    if date_of_birth:
        try:
            profile.date_of_birth = datetime.strptime(date_of_birth, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Update address fields
    if address:
        profile.address = address
    
    if department:
        profile.department = department
    
    if salary is not None:
        profile.salary = salary
    
    # Update bank details
    if bank_name:
        profile.bank_name = bank_name
    if bank_account_name:
        profile.bank_account_name = bank_account_name
    if bank_account_number:
        profile.bank_account_number = bank_account_number
    if bank_branch:
        profile.bank_branch = bank_branch
    if mpesa_number:
        profile.mpesa_number = mpesa_number
    
  
    # Update profile picture if provided
    if profile_picture:
        # Delete old profile picture if exists
        if profile.profile_picture and os.path.exists(profile.profile_picture):
            try:
                os.remove(profile.profile_picture)
            except:
                pass
        
        profile.profile_picture = save_admin_file(profile_picture, current_user.id, "profile")
    
    profile.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(profile)
    
    return profile

@router.put("/bank-details")
def update_bank_details(
    bank_name: str = Form(...),
    bank_account_name: str = Form(...),
    bank_account_number: str = Form(...),
    bank_branch: Optional[str] = Form(None),
    mpesa_number: Optional[str] = Form(None),
    
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update admin bank details for payments"""
    
    profile = db.query(AdminProfile).filter(AdminProfile.user_id == current_user.id).first()
    
    if not profile:
        raise HTTPException(
            status_code=404, 
            detail="Profile not found. Please create your profile first."
        )
    
    # Update bank details
    profile.bank_name = bank_name
    profile.bank_account_name = bank_account_name
    profile.bank_account_number = bank_account_number
    
    if bank_branch:
        profile.bank_branch = bank_branch
    if mpesa_number:
        profile.mpesa_number = mpesa_number
    
    profile.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "message": "Bank details updated successfully",
        "bank_details": {
            "bank_name": profile.bank_name,
            "account_name": profile.bank_account_name,
            "account_number": profile.bank_account_number,
            "branch": profile.bank_branch,
            "mpesa_number": profile.mpesa_number
        }
    }

@router.get("/bank-details")
def get_bank_details(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get admin's bank details"""
    
    profile = db.query(AdminProfile).filter(AdminProfile.user_id == current_user.id).first()
    
    if not profile:
        raise HTTPException(
            status_code=404, 
            detail="Profile not found"
        )
    
    return {
        "bank_details": {
            "bank_name": profile.bank_name,
            "account_name": profile.bank_account_name,
            "account_number": profile.bank_account_number,
            "branch": profile.bank_branch,
            "mpesa_number": profile.mpesa_number
        }
    }

# @router.put("/emergency-contact")
# def update_emergency_contact(
#     name: str = Form(...),
#     phone: str = Form(...),
#     relationship: str = Form(...),
    
#     current_user: User = Depends(require_admin),
#     db: Session = Depends(get_db)
# ):
#     """Update emergency contact information"""
    
#     profile = db.query(AdminProfile).filter(AdminProfile.user_id == current_user.id).first()
    
#     if not profile:
#         raise HTTPException(
#             status_code=404, 
#             detail="Profile not found"
#         )
    
#     profile.emergency_contact_name = name
#     profile.emergency_contact_phone = phone
#     profile.emergency_contact_relationship = relationship
#     profile.updated_at = datetime.utcnow()
    
#     db.commit()
    
#     return {
#         "message": "Emergency contact updated successfully",
#         "emergency_contact": {
#             "name": profile.emergency_contact_name,
#             "phone": profile.emergency_contact_phone,
#             "relationship": profile.emergency_contact_relationship
#         }
#     }

@router.put("/permissions")
def update_permissions(
    permissions: str = Form(...),  # JSON string
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update admin permissions (only for super admins)"""
    
    import json
    
    # Check if current user is super admin
    profile = db.query(AdminProfile).filter(AdminProfile.user_id == current_user.id).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")


###check if current permissions contains, manage_admins and si set as true i.e "manage_admin":
    if not profile.permissions.get("manage_admins", False):
        raise HTTPException(
            status_code=403, 
            detail="Only super admins can update permissions"
        )
    
    try:
        permissions_dict = json.loads(permissions)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    
    # Validate permissions structure
    valid_permissions = [
        "manage_users", "manage_workers", "manage_bookings", 
        "manage_payments", "view_reports", "system_settings",
        "manage_admins", "manage_hr", "manage_finance"
    ]
    
    for key in permissions_dict.keys():
        if key not in valid_permissions:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid permission key: {key}. Valid permissions: {', '.join(valid_permissions)}"
            )
    
    profile.permissions = permissions_dict
    profile.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "message": "Permissions updated successfully",
        "permissions": profile.permissions
    }


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
        func.date(User.last_seen) == datetime.utcnow().date()
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
    recent_users = db.query(User).order_by(User.last_seen.desc()).limit(5).all()
    recent_bookings = db.query(Booking).order_by(Booking.date_of_booking.desc()).limit(5).all()

    recent_users_data = [
        {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "last_seen": user.last_seen
        }
        for user in recent_users
    ]
    
    recent_bookings_data = [
        {
            "id": booking.id,
            "client_id": booking.client_id,
            "worker_id": booking.worker_id,
            "status": booking.status,
            "date_of_booking": booking.date_of_booking
        }
        for booking in recent_bookings
    ]
    
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
        "recent_users": recent_users_data,
        "recent_bookings": recent_bookings_data
    }

# ==========================
# USER MANAGEMENT
# ==========================
@router.get("/users", response_model=PaginatedUsersResponse)
def get_all_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    role: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    verified: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    query = db.query(User)

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

    offset = (page - 1) * limit
    total = query.count()

    users = (
        query
        .order_by(User.last_seen.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

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


    # admin/router.py - Add these endpoints to manage all admin payments
@router.post("/payments/create")
def create_admin_payment(
    admin_id: int = Form(...),
    amount: float = Form(...),
    payment_type: str = Form(..., regex="^(salary|bonus|commission|allowance)$"),
    payment_method: str = Form(..., regex="^(bank_transfer|mpesa|cash)$"),
    payment_period_start: Optional[str] = Form(None),
    payment_period_end: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a payment for an admin (only accessible by super admins or finance)"""
    
    # Check if current user has permission
    current_profile = db.query(AdminProfile).filter(
        AdminProfile.user_id == current_user.id
    ).first()
    
    if not current_profile or "manage_payments" not in current_profile.permissions:
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to create payments"
        )
    
    # Get the admin to pay
    admin_profile = db.query(AdminProfile).filter(AdminProfile.id == admin_id).first()
    if not admin_profile:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    # Parse dates if provided
    period_start = None
    period_end = None
    
    if payment_period_start:
        try:
            period_start = datetime.strptime(payment_period_start, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start date format")
    
    if payment_period_end:
        try:
            period_end = datetime.strptime(payment_period_end, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end date format")
    
    # Create payment
    payment = AdminPayment(
        admin_id=admin_id,
        amount=amount,
        payment_type=payment_type,
        payment_method=payment_method,
        payment_period_start=period_start,
        payment_period_end=period_end,
        notes=notes,
        bank_name=admin_profile.bank_name,
        bank_account_number=admin_profile.bank_account_number,
        status="pending"
    )
    
    db.add(payment)
    db.commit()
    db.refresh(payment)
    
    # Create notification for the admin
    notification = Notification(
        user_id=admin_profile.user_id,
        title="New Payment Created",
        message=f"A {payment_type} payment of KES {amount:,.2f} has been created for you.",
        is_read=False
    )
    db.add(notification)
    db.commit()
    
    return {
        "message": "Payment created successfully",
        "payment_id": payment.id,
        "status": payment.status
    }

@router.put("/payments/{payment_id}/process")
def process_admin_payment(
    payment_id: int,
    payment_date: str = Form(...),
    payment_reference: str = Form(...),
    mpesa_transaction_id: Optional[str] = Form(None),
    
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Process an admin payment (mark as completed)"""
    
    # Check permission
    current_profile = db.query(AdminProfile).filter(
        AdminProfile.user_id == current_user.id
    ).first()
    
    if not current_profile or "manage_payments" not in current_profile.permissions:
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to process payments"
        )
    
    payment = db.query(AdminPayment).filter(AdminPayment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Parse payment date
    try:
        pdate = datetime.strptime(payment_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payment date format")
    
    # Update payment
    payment.status = "completed"
    payment.payment_date = pdate
    payment.payment_reference = payment_reference
    payment.mpesa_transaction_id = mpesa_transaction_id
    payment.processed_at = datetime.utcnow()
    
    db.commit()
    
    # Create notification
    admin_user = db.query(User).filter(User.id == payment.admin_profile.user_id).first()
    if admin_user:
        notification = Notification(
            user_id=admin_user.id,
            title="Payment Processed",
            message=f"Your {payment.payment_type} payment of KES {payment.amount:,.2f} has been processed. Reference: {payment_reference}",
            is_read=False
        )
        db.add(notification)
        db.commit()
    
    return {"message": "Payment processed successfully"}

@router.get("/payments/all")
def get_all_admin_payments(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None),
    payment_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Get all admin payments (for finance/admin management)"""
    
    # Check permission
    current_profile = db.query(AdminProfile).filter(
        AdminProfile.user_id == current_user.id
    ).first()
    
    if not current_profile or "view_reports" not in current_profile.permissions:
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to view all payments"
        )
    
    query = db.query(AdminPayment).options(
        joinedload(AdminPayment.admin_profile)
    )
    
    # Apply filters
    if status:
        query = query.filter(AdminPayment.status == status)
    
    if payment_type:
        query = query.filter(AdminPayment.payment_type == payment_type)
    
    if start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(AdminPayment.created_at >= start)
    
    if end_date:
        end = datetime.strptime(end_date, "%Y-%m-%d")
        query = query.filter(AdminPayment.created_at <= end)
    
    payments = query.order_by(desc(AdminPayment.created_at)).all()
    
    # Summary statistics
    total_amount = sum(p.amount for p in payments)
    pending_amount = sum(p.amount for p in payments if p.status == "pending")
    completed_amount = sum(p.amount for p in payments if p.status == "completed")
    
    return {
        "payments": payments,
        "summary": {
            "total_payments": len(payments),
            "total_amount": float(total_amount),
            "pending_amount": float(pending_amount),
            "completed_amount": float(completed_amount),
            "average_payment": float(total_amount / len(payments)) if payments else 0
        }
    }