from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import uuid4
import shutil
import os
from datetime import datetime

from database import get_db
from models import (
    Workers, WorkerEmergencyContact, WorkerEquipment,
    WorkerService, WorkerAvailability, WorkerRating
)

router = APIRouter(prefix="/workers", tags=["workers"])

UPLOAD_DIR = "uploads/workers"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ------------------ CREATE WORKER ------------------
@router.post("/")
async def create_worker(
    db: Session = Depends(get_db),

    # --- Worker core ---
    user_id: int = Form(...),
    worker_type: str = Form(..., description="individual | organization"),
    first_name: str = Form(...),
    organization_name: Optional[str] = Form(None),
    organization_id: Optional[int] = Form(None),
    last_name: str = Form(...),
    phone_number: str = Form(...),
    address: Optional[str] = Form(None),
    mpesa_number: str = Form(...),

    bank_name: Optional[str] = Form(None),
    bank_account_name: Optional[str] = Form(None),
    bank_account_number: Optional[str] = Form(None),

    national_id_number: str = Form(...),
    agreement_accepted: bool = Form(False),

    profile_picture: Optional[UploadFile] = File(None),
    national_id_proof: Optional[UploadFile] = File(None),
    good_conduct_proof: Optional[UploadFile] = File(None),

    # --- Emergency contacts (comma separated JSON-like strings) ---
    emergency_contacts: Optional[str] = Form(None),  
    # example: '[{"name":"John","phone_number":"0712","relationship":"Brother"}]'

    # --- Equipments ---
    equipments: Optional[str] = Form(None),  
    # example: '[{"equipment_name":"Vacuum","has_equipment":true}]'

    # --- Services ---
    services: Optional[str] = Form(None),  
    # example: '[{"category_id":1,"experience_years":3}]'

    # --- Availability ---
    availabilities: Optional[str] = Form(None),  
    # example: '[{"day_of_week":0,"start_time":"08:00","end_time":"17:00"}]'
):
    print("here is availabilities:", availabilities)
    import json

    # Save files if uploaded
    def save_file(upload: UploadFile, folder: str):
        if not upload:
            return None
        file_path = os.path.join(UPLOAD_DIR, f"{folder}_{uuid4()}_{upload.filename}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload.file, buffer)
        return file_path

    worker = Workers(
        user_id=user_id,
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        worker_type=worker_type,
        organization_name=organization_name,
        organization_id=organization_id,
        address=address,
        mpesa_number=mpesa_number,
        bank_name=bank_name,
        bank_account_name=bank_account_name,
        bank_account_number=bank_account_number,
        national_id_number=national_id_number,
        agreement_accepted=agreement_accepted,
        profile_picture=save_file(profile_picture, "profile") if profile_picture else None,
        national_id_proof=save_file(national_id_proof, "id") if national_id_proof else None,
        good_conduct_proof=save_file(good_conduct_proof, "good_conduct") if good_conduct_proof else None,
    )

    db.add(worker)
    db.commit()
    db.refresh(worker)

    # ---------------- Related tables ----------------
    if emergency_contacts:
        contacts = json.loads(emergency_contacts)
        for c in contacts:
            db.add(WorkerEmergencyContact(
                worker_id=worker.id,
                name=c["name"],
                phone_number=c["phone_number"],
                relationship_to_worker=c.get("relationship_to_worker")
            ))

    if equipments:
        eqs = json.loads(equipments)
        for e in eqs:
            db.add(WorkerEquipment(
                worker_id=worker.id,
                equipment_name=e["equipment_name"],
                has_equipment=e.get("has_equipment", True)
            ))

    if services:
        svcs = json.loads(services)
        for s in svcs:
            db.add(WorkerService(
                worker_id=worker.id,
                category_id=s["category_id"],
                experience_years=s.get("experience_years", 0)
            ))

    if availabilities and availabilities.strip():
        avs = json.loads(availabilities)
        for a in avs:
            db.add(WorkerAvailability(
                worker_id=worker.id,
                day_of_week=a["day_of_week"],
                start_time=a["start_time"],
                end_time=a["end_time"]
            ))

    db.commit()

    return {"message": "Worker created successfully", "worker_id": worker.public_id}


# ------------------ ADD RATING ------------------
@router.post("/{worker_id}/ratings")
def add_rating(worker_id: int, rating: float = Form(...), review: Optional[str] = Form(None),
               booking_id: Optional[int] = Form(None), db: Session = Depends(get_db)):

    worker = db.query(Workers).filter(Workers.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    new_rating = WorkerRating(
        worker_id=worker.id,
        booking_id=booking_id,
        rating=rating,
        review=review
    )
    db.add(new_rating)

    # Update worker average rating
    all_ratings = [r.rating for r in worker.ratings] + [rating]
    worker.average_rating = sum(all_ratings) / len(all_ratings)

    db.commit()
    db.refresh(worker)

    return {"message": "Rating added", "average_rating": worker.average_rating}


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Workers
from schemas import (
    WorkerCreate,
    WorkerUpdate,
    WorkerResponse
)

router = APIRouter(
    prefix="/workers",
    tags=["workers"]
)


# ==========================
#  Create Worker
# ==========================
@router.post("/", response_model=WorkerResponse)
def create_worker(worker: WorkerCreate, db: Session = Depends(get_db)):
    db_worker = Workers(
        user_id=worker.user_id,
        worker_type=worker.worker_type,
        first_name=worker.first_name,
        last_name=worker.last_name,
        organization_name=worker.organization_name,
        phone_number=worker.phone_number,
        address=worker.address,
        profile_picture=worker.profile_picture,
        national_id_number=worker.national_id_number,
        national_id_proof=worker.national_id_proof,
        good_conduct_number=worker.good_conduct_number,
        good_conduct_proof=worker.good_conduct_proof,
        good_conduct_issue_date=worker.good_conduct_issue_date,
        good_conduct_expiry_date=worker.good_conduct_expiry_date,
        mpesa_number=worker.mpesa_number,
        bank_name=worker.bank_name,
        bank_account_name=worker.bank_account_name,
        bank_account_number=worker.bank_account_number,
    )
    db.add(db_worker)
    db.commit()
    db.refresh(db_worker)
    return db_worker


# ==========================
#  Get All Workers
# ==========================
@router.get("/", response_model=List[WorkerResponse])
def list_workers(db: Session = Depends(get_db)):
    return db.query(Workers).all()


# ==========================
#  Get Worker by ID
# ==========================
@router.get("/{worker_id}", response_model=WorkerResponse)
def get_worker(worker_id: int, db: Session = Depends(get_db)):
    worker = db.query(Workers).filter(Workers.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    return worker


# ==========================
#  Update Worker
# ==========================
@router.put("/{worker_id}", response_model=WorkerResponse)
def update_worker(worker_id: int, worker_update: WorkerUpdate, db: Session = Depends(get_db)):
    worker = db.query(Workers).filter(Workers.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    for field, value in worker_update.dict(exclude_unset=True).items():
        setattr(worker, field, value)

    db.commit()
    db.refresh(worker)
    return worker


# ==========================
#  Delete Worker
# ==========================
@router.delete("/{worker_id}")
def delete_worker(worker_id: int, db: Session = Depends(get_db)):
    worker = db.query(Workers).filter(Workers.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    db.delete(worker)
    db.commit()
    return {"message": "Worker deleted successfully"}