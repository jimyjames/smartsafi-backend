from fastapi import APIRouter
from database import get_db
from models import WorkerWallet,WorkerLedger,WorkerLoan
from sqlalchemy.orm import Session
from schemas import  BookingCreate, BookingResponse, BookingRequestCreate,BookingRequestUpdate,BookingRequestResponse,BookingUpdate,BookingBase,WorkerRatingBase

booking_router = APIRouter(prefix="/bookings", tags=["bookings"]) 
jobs_router = APIRouter(prefix="/jobs", tags=["jobs"])


def process_worker_earning(worker_id: int, amount: float, booking_id: int, db: Session):
    wallet = db.query(WorkerWallet).filter_by(worker_id=worker_id).first()
    if not wallet:
        wallet = WorkerWallet(worker_id=worker_id, balance=0)
        db.add(wallet)

    loan = (
        db.query(WorkerLoan)
        .filter_by(worker_id=worker_id, status="active", auto_deduct=True)
        .first()
    )

    deduction = 0
    if loan:
        deduction = min(
            amount * loan.repayment_rate,
            loan.total_payable - loan.amount_paid
        )

        loan.amount_paid += deduction
        if loan.amount_paid >= loan.total_payable:
            loan.status = "repaid"

        db.add(WorkerLedger(
            worker_id=worker_id,
            amount=deduction,
            type="debit",
            reason="loan_repayment",
            reference=f"booking:{booking_id}",
            description="Automatic loan deduction"
        ))

    net_amount = amount - deduction
    wallet.balance += net_amount

    db.add(WorkerLedger(
        worker_id=worker_id,
        amount=net_amount,
        type="credit",
        reason="job_payment",
        reference=f"booking:{booking_id}",
        description="Job payment credited"
    ))

    db.commit()
