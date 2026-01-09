# from . import router

from models import WorkerLedger,WorkerLoan,WorkerWallet
from database import get_db
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException,APIRouter

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.get("/")
def test():
    return {"message": "wallet"}

# def get_wallets(db: Session = Depends(get_db)):
#     wallets = db.query(WorkerWallet).all()
#     return wallets


@router.get("/{worker_id}")
def get_wallet(worker_id: int, db: Session = Depends(get_db)):
    wallet = db.query(WorkerWallet).filter_by(worker_id=worker_id).first()
    if not wallet:
        wallet = WorkerWallet(worker_id=worker_id, balance=0.0)
        db.add(wallet)
        db.commit()
        db.refresh(wallet)

    return {
        "worker_id": worker_id,
        "balance": wallet.balance
    }


@router.get("/ledger/{worker_id}")
def get_ledger(worker_id: int, db: Session = Depends(get_db)):
    ledger = (
        db.query(WorkerLedger)
        .filter(WorkerLedger.worker_id == worker_id)
        .order_by(WorkerLedger.created_at.desc())
        .all()
    )

    return ledger


@router.post("/loan/borrow")
def borrow_money(
    worker_id: int,
    amount: float,
    interest: float = 0.0,
    db: Session = Depends(get_db)
):
    total = amount + interest

    loan = WorkerLoan(
        worker_id=worker_id,
        principal=amount,
        interest=interest,
        total_payable=total
    )
    db.add(loan)

    wallet = db.query(WorkerWallet).filter_by(worker_id=worker_id).first()
    if not wallet:
        wallet = WorkerWallet(worker_id=worker_id, balance=0.0)
        db.add(wallet)

    wallet.balance += amount

    ledger = WorkerLedger(
        worker_id=worker_id,
        amount=amount,
        type="credit",
        reason="loan_disbursement",
        reference=f"loan:{loan.id}",
        description="Loan credited to wallet"
    )
    db.add(ledger)

    db.commit()
    return {"message": "Loan issued", "loan_id": loan.id}


@router.post("/loan/repay")
def repay_loan(
    loan_id: int,
    amount: float,
    db: Session = Depends(get_db)
):
    loan = db.query(WorkerLoan).filter_by(id=loan_id).first()
    if not loan or loan.status != "active":
        raise HTTPException(status_code=400, detail="Invalid loan")

    wallet = db.query(WorkerWallet).filter_by(worker_id=loan.worker_id).first()
    if wallet.balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    loan.amount_paid += amount
    wallet.balance -= amount

    if loan.amount_paid >= loan.total_payable:
        loan.status = "repaid"

    ledger = WorkerLedger(
        worker_id=loan.worker_id,
        amount=amount,
        type="debit",
        reason="loan_repayment",
        reference=f"loan:{loan.id}",
        description="Loan repayment"
    )

    db.add(ledger)
    db.commit()

    return {"message": "Loan repayment successful"}
