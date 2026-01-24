from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status,APIRouter, Form
from sqlalchemy.orm import Session,joinedload
from sqlalchemy import func
from datetime import datetime
from schemas import ClientCreate, ClientOut, ClientBase
from models import Client,User,Booking,Payment,Workers,ServiceFeature
from database import SessionLocal, get_db  
from pathlib import Path
import shutil
from typing import Optional



router = APIRouter(prefix="/clients", tags=["clients"])



UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)



@router.post("/", response_model=ClientOut)
def register_client_with_files(
    user_id: int = Form(...),
    client_type: str = Form(...),  # "individual" or "organization"
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    organization_name: Optional[str] = Form(None),
    tax_number: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    national_id_number: Optional[int] = Form(None),
    address: Optional[str] = Form(None),

    national_id_proof: UploadFile = File(...),
    tax_document_proof: UploadFile = File(None),
    profile_picture: UploadFile = File(None),

    db: Session = Depends(get_db)
):
    print
    # 1. Validate user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Check existing client
    if db.query(Client).filter(Client.user_id == user_id).first():
        raise HTTPException(status_code=403, detail="Client already exists")

    # 3. Validate fields based on client_type
    if client_type == "individual":
        if not first_name or not last_name:
            raise HTTPException(status_code=422, detail="first_name and last_name are required for individual clients.")
    elif client_type == "organization":
        if not organization_name or not tax_number:
            raise HTTPException(status_code=422, detail="organization_name and tax_number are required for organizations.")
    else:
        raise HTTPException(status_code=422, detail="Invalid client_type. Must be 'individual' or 'organization'.")

    # 4. Create client record
    client = Client(
        user_id=user_id,
        client_type=client_type,
        first_name=first_name,
        last_name=last_name,
        organization_name=organization_name,
        tax_number=tax_number,
        phone_number=phone_number,
        national_id_number=national_id_number,
        address=address,
        verification_id=False,
        verification_tax=False
    )
    db.add(client)
    db.commit()
    db.refresh(client)

    # 5. Save uploaded files
    client_folder = UPLOAD_DIR / f"client_{user_id}"
    client_folder.mkdir(parents=True, exist_ok=True)

    def save_file(file: UploadFile, prefix: str) -> str:
        path = client_folder / f"{prefix}_{file.filename}"
        with open(path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        return str(path)

    client.national_id_proof = save_file(national_id_proof, "id")
    if tax_document_proof:
         client.tax_document_proof = save_file(tax_document_proof, "tax")
    if profile_picture:
        client.profile_picture = save_file(profile_picture, "profile")

    db.commit()
    db.refresh(client)
    return client

@router.get("/{client_id}", response_model=ClientOut)
def get_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.user_id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@router.get("/", response_model=list[ClientOut])    
def get_clients(db: Session = Depends(get_db)):
    clients = db.query(Client).all()
    return clients
@router.put("/{client_id}", response_model=ClientOut)
def update_client(client_id: int, client: ClientBase, db: Session = Depends(get_db)):
    db_client = db.query(Client).filter(Client.client_id == client_id).first()
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")
    for key, value in client.dict().items():
        setattr(db_client, key, value)
    db.commit()
    db.refresh(db_client)
    return db_client


router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(client_id: int, db: Session = Depends(get_db)):
    db_client = db.query(Client).filter(Client.client_id == client_id).first()
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")
    db.delete(db_client)
    db.commit()
    return {"message": "Client deleted successfully"}



@router.get("/admin/")
def get_clients_analytics(db: Session = Depends(get_db)):
    clients = (
        db.query(Client)
        .options(
            joinedload(Client.user),
            joinedload(Client.bookings)
                .joinedload(Booking.feature),
            joinedload(Client.bookings)
                .joinedload(Booking.worker)
        )
        .all()
    )

    result = []

    for client in clients:
        bookings = client.bookings or []

        completed = [b for b in bookings if b.status == "completed"]

        total_bookings = len(bookings)
        total_spent = sum(b.total_price for b in completed)

        average_booking_value = (
            total_spent / len(completed)
            if completed else None
        )

        last_booking = (
            max(b.appointment_datetime for b in bookings)
            if bookings else None
        )

        upcoming_bookings = len([
            b for b in bookings
            if b.appointment_datetime > datetime.utcnow()
        ])

        cancellations = len([
            b for b in bookings if b.status == "cancelled"
        ])

        cancellation_rate = (
            (cancellations / total_bookings) * 100
            if total_bookings else None
        )

        # Refunds
        refund_data = (
            db.query(
                func.coalesce(func.sum(Payment.amount), 0),
                func.count(Payment.id)
            )
            .filter(
                Payment.booking_id.in_([b.id for b in bookings]),
                Payment.type == "refund"
            )
            .first()
        )

        total_refunded, refund_count = refund_data

        # Recent bookings (last 5)
        recent_bookings = sorted(
            bookings,
            key=lambda b: b.appointment_datetime,
            reverse=True
        )[:5]

        result.append({
            "id": client.public_id,
            "name": (
                f"{client.first_name} {client.last_name}"
                if client.first_name else client.organization_name
            ),
            "email": client.user.email,
            "phone": client.phone_number,
            "location": client.address,

            # Status
            "status": "active" if total_bookings > 0 else "inactive",

            # Booking analytics
            "totalBookings": total_bookings,
            "totalSpent": total_spent,
            "averageBookingValue": average_booking_value,
            "lastBookingDate": (
                last_booking.isoformat() if last_booking else None
            ),
            "upcomingBookings": upcoming_bookings,
            "cancellationRate": cancellation_rate,

            # Financial
            "outstandingBalance": None,
            "totalRefunded": total_refunded,
            "refundCount": refund_count,

            # Preferences (not in DB yet)
            "preferredContact": None,
            "language": None,
            "notificationsEnabled": None,
            "marketingOptIn": None,

            # Relationship / CRM (not in DB yet)
            "customerSegment": None,
            "lifetimeValue": total_spent,
            "churnRisk": None,
            "referralCount": None,

            # Favorites (derived, DB-backed)
            "favoriteServices": list({
                b.feature.title for b in completed if b.feature
            }),
            "preferredProfessionals": list({
                f"{b.worker.first_name} {b.worker.last_name}"
                for b in completed if b.worker
            }),

            # Recent bookings
            "recentBookings": [
                {
                    "id": b.id,
                    "date": b.appointment_datetime.isoformat(),
                    "service": b.feature.title if b.feature else None,
                    "professional": (
                        f"{b.worker.first_name} {b.worker.last_name}"
                        if b.worker else None
                    ),
                    "amount": b.total_price,
                    "status": b.status
                }
                for b in recent_bookings
            ]
        })

    return result

