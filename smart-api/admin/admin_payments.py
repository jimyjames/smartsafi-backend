# admin/payments.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from sqlalchemy import func, desc
from datetime import datetime, timedelta

from database import get_db
from models import User, AdminProfile, AdminPayment
from authentication import require_admin
from schemas import (
    AdminPaymentCreate,
    AdminPaymentResponse,
    AdminPaymentSummary,
    AdminEarningsResponse
)

router = APIRouter(prefix="/admin/payments", tags=["admin-payments"])

# ==========================
# ADMIN PAYMENTS MODEL
# ==========================
# Add this to your models.py

# ==========================
# ADMIN PAYMENTS ENDPOINTS
# ==========================
@router.get("/my-payments", response_model=List[AdminPaymentResponse])
def get_my_payments(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None, ge=1, le=12),
    payment_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """Get payment history for the current admin"""
    
    # Get admin profile
    profile = db.query(AdminProfile).filter(AdminProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Admin profile not found")
    
    query = db.query(AdminPayment).filter(AdminPayment.admin_id == profile.id)
    
    # Apply filters
    if year:
        query = query.filter(func.extract('year', AdminPayment.created_at) == year)
    
    if month:
        query = query.filter(func.extract('month', AdminPayment.created_at) == month)
    
    if payment_type:
        query = query.filter(AdminPayment.payment_type == payment_type)
    
    if status:
        query = query.filter(AdminPayment.status == status)
    
    payments = query.order_by(desc(AdminPayment.created_at)).all()
    
    return payments

@router.get("/my-earnings", response_model=AdminEarningsResponse)
def get_my_earnings(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Get earnings summary for the current admin"""
    
    # Get admin profile
    profile = db.query(AdminProfile).filter(AdminProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Admin profile not found")
    
    query = db.query(AdminPayment).filter(
        AdminPayment.admin_id == profile.id,
        AdminPayment.status == "completed"
    )
    
    if start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(AdminPayment.payment_date >= start)
    
    if end_date:
        end = datetime.strptime(end_date, "%Y-%m-%d")
        query = query.filter(AdminPayment.payment_date <= end)
    
    payments = query.all()
    
    # Calculate totals by payment type
    salary_total = sum(p.amount for p in payments if p.payment_type == "salary")
    bonus_total = sum(p.amount for p in payments if p.payment_type == "bonus")
    commission_total = sum(p.amount for p in payments if p.payment_type == "commission")
    allowance_total = sum(p.amount for p in payments if p.payment_type == "allowance")
    
    total_earnings = salary_total + bonus_total + commission_total + allowance_total
    
    # Current month earnings
    today = datetime.utcnow()
    first_day_of_month = today.replace(day=1)
    
    current_month_payments = db.query(AdminPayment).filter(
        AdminPayment.admin_id == profile.id,
        AdminPayment.status == "completed",
        AdminPayment.payment_date >= first_day_of_month
    ).all()
    
    current_month_total = sum(p.amount for p in current_month_payments)
    
    # Last month earnings
    first_day_last_month = (first_day_of_month - timedelta(days=1)).replace(day=1)
    last_day_last_month = first_day_of_month - timedelta(days=1)
    
    last_month_payments = db.query(AdminPayment).filter(
        AdminPayment.admin_id == profile.id,
        AdminPayment.status == "completed",
        AdminPayment.payment_date >= first_day_last_month,
        AdminPayment.payment_date <= last_day_last_month
    ).all()
    
    last_month_total = sum(p.amount for p in last_month_payments)
    
    # Calculate percentage change
    percentage_change = 0
    if last_month_total > 0:
        percentage_change = ((current_month_total - last_month_total) / last_month_total) * 100
    
    return {
        "admin_id": profile.id,
        "admin_name": f"{profile.first_name} {profile.last_name}",
        "total_earnings": float(total_earnings),
        "current_month_total": float(current_month_total),
        "last_month_total": float(last_month_total),
        "percentage_change": round(percentage_change, 2),
        "breakdown": {
            "salary": float(salary_total),
            "bonus": float(bonus_total),
            "commission": float(commission_total),
            "allowance": float(allowance_total)
        },
        "salary": profile.salary,
        "payment_count": len(payments)
    }

@router.get("/my-upcoming-payments", response_model=List[AdminPaymentResponse])
def get_upcoming_payments(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get upcoming payments for the current admin"""
    
    # Get admin profile
    profile = db.query(AdminProfile).filter(AdminProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Admin profile not found")
    
    # Get pending payments
    pending_payments = db.query(AdminPayment).filter(
        AdminPayment.admin_id == profile.id,
        AdminPayment.status == "pending"
    ).order_by(AdminPayment.created_at).all()
    
    return pending_payments

@router.get("/payslip/{payment_id}")
def get_payslip(
    payment_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get detailed payslip for a specific payment"""
    
    # Get admin profile
    profile = db.query(AdminProfile).filter(AdminProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Admin profile not found")
    
    payment = db.query(AdminPayment).filter(
        AdminPayment.id == payment_id,
        AdminPayment.admin_id == profile.id
    ).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Calculate deductions (example - you'd adjust based on your business rules)
    basic_salary = payment.amount
    paye = basic_salary * 0.1  # 10% PAYE (example)
    nssf = basic_salary * 0.06  # 6% NSSF (example)
    nhif = 500  # Fixed NHIF (example)
    total_deductions = paye + nssf + nhif
    net_salary = basic_salary - total_deductions
    
    return {
        "payslip_id": f"PS{payment.id:06d}",
        "employee_details": {
            "name": f"{profile.first_name} {profile.last_name}",
            "employee_id": profile.employee_id,
            "department": profile.department,
            "position": profile.position
        },
        "payment_details": {
            "payment_date": payment.payment_date,
            "payment_period": f"{payment.payment_period_start} to {payment.payment_period_end}",
            "payment_type": payment.payment_type,
            "payment_method": payment.payment_method,
            "reference": payment.payment_reference
        },
        "earnings": {
            "basic_salary": float(basic_salary),
            "bonus": 0.0,  # Adjust based on your system
            "allowance": 0.0,
            "overtime": 0.0,
            "total_earnings": float(basic_salary)
        },
        "deductions": {
            "paye": float(paye),
            "nssf": float(nssf),
            "nhif": float(nhif),
            "total_deductions": float(total_deductions)
        },
        "net_salary": float(net_salary),
        "bank_details": {
            "bank_name": profile.bank_name,
            "account_name": profile.bank_account_name,
            "account_number": profile.bank_account_number
        }
    }