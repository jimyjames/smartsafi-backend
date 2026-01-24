from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from sqlalchemy import func
from uuid import uuid4
import shutil
import os
from datetime import datetime, timedelta


from database import get_db
from models import (
    Workers, WorkerEmergencyContact, WorkerEquipment,WorkerPayments,
    WorkerService, WorkerAvailability, WorkerRating, Notification, User, WorkerLanguages,Booking
)

from bookings.route import get_worker_job_counts,get_worker_bookings
from notifications.route import get_worker_notifications

from schemas import (
    EarningsSummaryResponse,
    NotificationResponse,
    WorkerCreate,
    WorkerRatingCreate,
    WorkerPaymentCreate,
    WorkerUpdate,
    WorkerResponse,
    WorkerEmergencyContactCreate,WorkerEquipmentCreate,
    WorkerRatingResponse,
    WorkerReviewStatsResponse,EarningsChartItem,WorkerReviewRatingResponse
)
router = APIRouter(prefix="/workers", tags=["workers"])




UPLOAD_DIR = "uploads/workers"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ------------------ CREATE WORKER ------------------
@router.post("")
# async def create_worker(
def create_worker(
    db: Session = Depends(get_db),

    # --- Worker core ---
    user_id: int = Form(...),
    worker_type: str = Form(..., description="individual | organization"),
    first_name: Optional[str] = Form(None),
    organization_name: Optional[str] = Form(None),
    organization_id: Optional[int] = Form(None),
    last_name: Optional[str] = Form(None),
    phone_number: str= Form(...),
    address: Optional[str] = Form(None),
    mpesa_number: str = Form(...),
    company_hotline_number: Optional[str] = Form(None),

    bank_name: Optional[str] = Form(None),
    bank_account_name: Optional[str] = Form(None),
    bank_account_number: Optional[str] = Form(None),

    national_id_number: Optional[str] = Form(None),
    company_registration_number: Optional[str] = Form(None),
    agreement_accepted: bool = Form(False),
    location_pin: Optional[str] = Form(None),

    profile_picture: Optional[UploadFile] = File(None),
    # national_id_proof: Optional[UploadFile] = File(None),
    national_id_front: Optional[UploadFile] = File(None),
    national_id_back: Optional[UploadFile] = File(None),

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
    print("here is availabilities:",)
    # availabilities)

    if worker_type not in ["individual", "organization"]:
        raise HTTPException(status_code=400, detail="Invalid worker type")
    if worker_type == "individual" and (not first_name or not last_name or not national_id_number):
        raise HTTPException(status_code=400, detail="First and last names are required for individual workers")
    if worker_type == "organization" and (not organization_name or not company_registration_number or not company_hotline_number):
        raise HTTPException(status_code=400, detail="Organization name, company registration number, and company hotline number are required for worker organization ")
    if not agreement_accepted:
        raise HTTPException(status_code=400, detail="You must accept the agreement to proceed")
    if not mpesa_number:
        raise HTTPException(status_code=400, detail="Mpesa number is required")
    if not phone_number:
        raise HTTPException(status_code=400, detail="Phone number is required")
    if not location_pin:
        raise HTTPException(status_code=400, detail="Location pin is required")
    if db.query(Workers).filter(Workers.user_id == user_id).first():
        raise HTTPException(status_code=403, detail="Worker profile already exists for this user")
    

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
        # national_id_proof=save_file(national_id_proof, "id") if national_id_proof else None,
        national_id_front=save_file(national_id_front, "id_front") if national_id_front else None,
        national_id_back=save_file(national_id_back, "id_back") if national_id_back else None,
        good_conduct_proof=save_file(good_conduct_proof, "good_conduct") if good_conduct_proof else None,
    )

    db.add(worker)
    db.commit()
    db.refresh(worker)

    # ---------------- Related tables ----------------
    if emergency_contacts:
        try:
            contacts = json.loads(emergency_contacts)

            # If a single dict is sent instead of a list
            if isinstance(contacts, dict):
                contacts = [contacts]

            for c in contacts:
                db.add(WorkerEmergencyContact(
                    worker_id=worker.id,
                    name=c.get("name"),
                    phone_number=c.get("phone_number"),
                    relationship_to_worker=c.get("relationship") or c.get("relationship_to_worker")
                ))

        except json.JSONDecodeError:
            # If user accidentally sends raw text fields instead of JSON
            db.add(WorkerEmergencyContact(
                worker_id=worker.id,
                name=emergency_contacts,
                phone_number=None,
                relationship_to_worker=None
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

    # if availabilities and availabilities.strip():
    #     avs = json.loads(availabilities)
    #     for a in avs:
    #         db.add(WorkerAvailability(
    #             worker_id=worker.id,
    #             day_of_week=a["day_of_week"],
    #             start_time=a["start_time"],
    #             end_time=a["end_time"]
    #         ))
    if availabilities:
        avs = json.loads(availabilities)
        for a in avs:
            db.add(WorkerAvailability(
                worker_id=worker.id,
                day_of_week=a["day_of_week"]
            ))



    db.commit()

    return {"message": "Worker created successfully", "worker_id": worker.public_id}


# ------------------ ADD RATING ------------------
@router.post("/{worker_id}/ratings")
def add_rating(worker_id: int, Workerrating: WorkerRatingCreate, db: Session = Depends(get_db)):

    worker = db.query(Workers).filter(Workers.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    booking_id = Workerrating.booking_id
    rating = Workerrating.rating
    review = Workerrating.review
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





# ==========================
#  Get All Workers
# ==========================
@router.get("/", response_model=List[WorkerResponse])
def list_workers(db: Session = Depends(get_db)):
    return db.query(Workers).all()


# ==========================



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



@router.get("/{worker_id}", response_model=WorkerResponse)
def get_full_worker(worker_id: int, db: Session = Depends(get_db)):
    worker = (
        db.query(Workers)
        .options(
            joinedload(Workers.emergency_contacts),
            joinedload(Workers.equipments),
            joinedload(Workers.services),
            joinedload(Workers.availabilities),
            joinedload(Workers.ratings),
            joinedload(Workers.languages).joinedload(WorkerLanguages.language),
            joinedload(Workers.user).joinedload(User.notifications).joinedload(Notification.user),
            # joinedload(User.notifications).joinedload(Notification.user),
        )
        .filter(Workers.id == worker_id)
        .first()
    )

    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    # Get job stats
    job_stats = get_worker_job_counts(worker_id, db)
    worker.job_stats = job_stats

    return worker


#### get worker jobs ####

@router.get("/{worker_id}/jobs")
def grouped_worker_jobs(worker_id: int, db: Session = Depends(get_db)):
    print("Fetching jobs for worker:", worker_id)
    return get_worker_bookings(worker_id, db)


    ##### Worker equipments #####

#UPLOAD_DIR = "static/equipment_images"

@router.post("/{worker_id}/equipments", response_model=dict)
def add_worker_equipment(
    worker_id: int,
    equipment_name: str = Form(...),
    has_equipment: bool = Form(True),
    equipment_description: str = Form(None),
    equipment_status: str = Form(None),
    equipment_image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    worker = db.query(Workers).filter(Workers.id == worker_id).first()
    if equipment_name is None or equipment_name.strip() == "":
        raise HTTPException(status_code=400, detail="Equipment name is required")
    if equipment_status is None or equipment_status.strip() == "":
        raise HTTPException(status_code=400, detail="Equipment status is required")
    if has_equipment is None:
        raise HTTPException(status_code=400, detail="has_equipment field is required")
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    

    image_path = None
    if equipment_image:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        filename = f"{uuid4()}_{equipment_image.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(equipment_image.file, buffer)
        image_path = file_path

    db_equipment = WorkerEquipment(
        worker_id=worker.id,
        equipment_name=equipment_name,
        has_equipment=has_equipment,
        equipment_description=equipment_description,
        equipment_status=equipment_status,
        equipment_image=image_path
    )

    db.add(db_equipment)
    db.commit()
    db.refresh(db_equipment)

    return {
        "message": "Equipment added successfully",
        "equipment": {
            "id": db_equipment.id,
            "equipment_name": db_equipment.equipment_name,
            "equipment_image": db_equipment.equipment_image,
            "equipment_status": db_equipment.equipment_status
        }
    }
    
@router.delete("/equipments/{equipment_id}", status_code=204)
def delete_worker_equipment(equipment_id: int, db: Session = Depends(get_db)):
    equipment = db.query(WorkerEquipment).filter(WorkerEquipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    db.delete(equipment)
    db.commit()
    return {"message": "Equipment deleted successfully"}


# @router.get("/{worker_id}/reviews", response_model=List[WorkerRatingResponse])
# def get_worker_reviews(worker_id: int, db: Session = Depends(get_db)):
#     worker = db.query(Workers).filter(Workers.id == worker_id).first()
#     if not worker:
#         raise HTTPException(status_code=404, detail="Worker not found")
#     reviews= db.query(WorkerRating).filter(WorkerRating.worker_id == worker_id).all()
#     return reviews
from sqlalchemy.orm import selectinload
@router.get("/{worker_id}/reviews", response_model=List[WorkerRatingResponse])
def get_worker_ratings(worker_id: int, db: Session = Depends(get_db)):
    ratings = db.query(WorkerRating).options(
        selectinload(WorkerRating.booking).selectinload(Booking.client)
    ).filter(WorkerRating.worker_id == worker_id).all()

    return ratings
    

@router.get(
    "/{worker_id}/review-stats",
    response_model=WorkerReviewStatsResponse
)
def get_worker_review_stats(
    worker_id: int,
    db: Session = Depends(get_db)
):
    # Ensure worker exists
    worker = db.query(Workers).filter(Workers.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    # Total reviews
    total_reviews = (
        db.query(func.count(WorkerRating.id))
        .filter(WorkerRating.worker_id == worker_id)
        .scalar()
    )

    if total_reviews == 0:
        return {
            "totalReviews": 0,
            "averageRating": 0.0,
            "responseRate": 0,
            "ratingBreakdown": {5: 0, 4: 0, 3: 0, 2: 0, 1: 0},
        }

    # Average rating
    average_rating = (
        db.query(func.avg(WorkerRating.rating))
        .filter(WorkerRating.worker_id == worker_id)
        .scalar()
    )

    # Rating breakdown
    breakdown_raw = (
        db.query(
            WorkerRating.rating,
            func.count(WorkerRating.rating)
        )
        .filter(WorkerRating.worker_id == worker_id)
        .group_by(WorkerRating.rating)
        .all()
    )

    rating_breakdown = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    for rating, count in breakdown_raw:
        rating_breakdown[int(rating)] = count

    # Response rate (example logic)
    # Adjust if you have `responded_at` or similar field
    response_rate = 95  # placeholder / business rule

    return {
        "totalReviews": total_reviews,
        "averageRating": round(float(average_rating), 1),
        "responseRate": response_rate,
        "ratingBreakdown": rating_breakdown,
    }


@router.get("/{worker_id}/notifications", response_model=List[NotificationResponse])
def get_worker_notifications(worker_id: int, db: Session = Depends(get_db)):
    worker = db.query(Workers).filter(Workers.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    notifications = (db.query(Booking).filter(Booking.worker_id == worker_id, Booking.status == "pending").all())
    return notifications

@router.get("/{worker_id}/notifications/", response_model=List[NotificationResponse])
def notifications_getter(worker_id: int, db: Session = Depends(get_db)):
    return get_worker_notifications(worker_id, db)


####### get my  payments ######
# @router.get("/{worker_id}/payments")
# def get_worker_payments(worker_id: int, db: Session = Depends(get_db)):
#     worker = db.query(Workers).filter(Workers.id == worker_id).first()
#     if not worker:
#         raise HTTPException(status_code=404, detail="Worker not found")
#     # Assuming WorkerWallet and WorkerLedger models exist
#    worker_payments= db.query(WorkerPayments).filter(WorkerPayments.worker_id == worker_id).all()
#     return worker_payments


######make worker payments
@router.post("/{worker_id}/payments")
def make_worker_payment(worker_id: int, payment: WorkerPaymentCreate, db: Session = Depends(get_db)):
    worker = db.query(Workers).filter(Workers.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    amount = payment.amount
    payment_method = payment.payment_method
    new_payment = WorkerPayments(
        worker_id=worker.id,
        amount=amount,
        payment_method=payment_method,
        payment_date=datetime.utcnow(),
        work_done=payment.work_done
    )
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)

    return {"message": "Payment made successfully", "payment_id": new_payment.id}
 
def get_last_30_days_earnings(db: Session, worker_id: int):
    start_date = datetime.utcnow() - timedelta(days=30)

    results = (
        db.query(
            func.date(WorkerPayments.payment_date).label("day"),
            func.sum(WorkerPayments.amount).label("earnings")
        )
        .filter(
            WorkerPayments.worker_id == worker_id,
            WorkerPayments.payment_date >= start_date
        )
        .group_by(func.date(WorkerPayments.payment_date))
        .order_by(func.date(WorkerPayments.payment_date))
        .all()
    )

    return results
def format_chart_data(results):
    chart_data = []

    for index, row in enumerate(results, start=1):
        chart_data.append({
            "day": f"Day {index}",
            "earnings": float(row.earnings or 0)
        })

    return chart_data
@router.get(
    "/{worker_id}/earnings",
    response_model=List[EarningsChartItem]
)
def worker_earnings_chart(
    worker_id: int,
    db: Session = Depends(get_db)
):
    results = get_last_30_days_earnings(db, worker_id)
    return format_chart_data(results)


def start_of_week():
    today = datetime.utcnow()
    # return today - timedelta(days=today.weekday())
    return today - timedelta(days=today.weekday()+2)

def start_of_month():
    today = datetime.utcnow()
    return today.replace(day=1)



def total_earnings(db: Session, worker_id: int):
    return (
        db.query(func.coalesce(func.sum(WorkerPayments.amount), 0))
        .filter(WorkerPayments.worker_id == worker_id)
        .scalar()
    )

def weekly_earnings(db: Session, worker_id: int):
    start_this_week = start_of_week()
    start_last_week = start_this_week - timedelta(days=7)

    this_week = (
        db.query(func.coalesce(func.sum(WorkerPayments.amount), 0))
        .filter(
            WorkerPayments.worker_id == worker_id,
            WorkerPayments.payment_date >= start_this_week
        )
        .scalar()
    )
    print("This week earnings:", this_week)
    print("Start this week:", start_this_week)
    print("Start last week:", start_last_week)

    last_week = (
        db.query(func.coalesce(func.sum(WorkerPayments.amount), 0))
        .filter(
            WorkerPayments.worker_id == worker_id,
            WorkerPayments.payment_date >= start_last_week,
            WorkerPayments.payment_date < start_this_week
        )
        .scalar()
    )

    return this_week, last_week


def monthly_earnings(db: Session, worker_id: int):
    start_this_month = start_of_month()
    start_last_month = (start_this_month - timedelta(days=1)).replace(day=1)

    this_month = (
        db.query(func.coalesce(func.sum(WorkerPayments.amount), 0))
        .filter(
            WorkerPayments.worker_id == worker_id,
            WorkerPayments.payment_date >= start_this_month
        )
        .scalar()
    )

    last_month = (
        db.query(func.coalesce(func.sum(WorkerPayments.amount), 0))
        .filter(
            WorkerPayments.worker_id == worker_id,
            WorkerPayments.payment_date >= start_last_month,
            WorkerPayments.payment_date < start_this_month
        )
        .scalar()
    )

    return this_month, last_month


def pending_earnings(db: Session, worker_id: int):
    return (
        db.query(func.coalesce(func.sum(Booking.total_price), 0))
        .filter(
            Booking.worker_id == worker_id,
            Booking.status == "pending"
        )
        .scalar()
    )


def percentage_change(current: float, previous: float) -> float:
    if previous == 0:
        return 0.0
    return round(((current - previous) / previous) * 100, 2)



def build_earnings_summary(db: Session, worker_id: int):
    total = total_earnings(db, worker_id)

    this_week, last_week = weekly_earnings(db, worker_id)
    this_month, last_month = monthly_earnings(db, worker_id)

    pending = pending_earnings(db, worker_id)

    return {
        "total": total,
        "thisWeek": this_week,
        "thisMonth": this_month,
        "pending": pending,
        "lastWeekChange": percentage_change(this_week, last_week),
        "lastMonthChange": percentage_change(this_month, last_month),
    }


@router.get(
    "/{worker_id}/earnings-summary",
    response_model=EarningsSummaryResponse
)
def worker_earnings_summary(
    worker_id: int,
    db: Session = Depends(get_db)
):
    return build_earnings_summary(db, worker_id)


@router.get("/admin/all")
def list_cleaners_analytics(db: Session = Depends(get_db)):
    workers = (
        db.query(Workers)
        .options(
            joinedload(Workers.user),
            joinedload(Workers.availabilities),
            joinedload(Workers.ratings),
            joinedload(Workers.assigned_bookings)
        )
        .all()
    )

    response = []

    for worker in workers:
        bookings = worker.assigned_bookings or []

        total_jobs = len(bookings)

        # Average rating (DB truth)
        rating = (
            sum(r.rating for r in worker.ratings) / len(worker.ratings)
            if worker.ratings else 0
        )

        # Status (derived, not hardcoded)
        status = "active" if total_jobs > 0 else "inactive"

        # Vetting (derived from documents)
        id_verified = bool(worker.national_id_front and worker.national_id_back)
        background_check = bool(worker.good_conduct_proof)

        if id_verified and background_check:
            vetting_status = "verified"
        else:
            vetting_status = "pending"

        response.append({
            "id": worker.public_id,
            "name": (
                f"{worker.first_name} {worker.last_name}"
                if worker.worker_type == "individual"
                else worker.organization_name
            ),
            "email": worker.user.email if worker.user else None,
            "phone": worker.phone_number,
            "location": worker.address,

            "rating": round(rating, 1),
            "totalJobs": total_jobs,
            "status": status,

            # Vetting
            "vettingStatus": vetting_status,
            "idVerified": id_verified,
            "backgroundCheck": background_check,

            # Dates
            "joinedAt": (
                worker.created_at.isoformat()
                if hasattr(worker, "created_at") and worker.created_at
                else None
            ),

            # Onboarding (NOT IN DB)
            "onboardingStatus": None,
            "onboardingStep": None,
            "appliedDate": None,

            # Availability
            "availability": [
                {
                    "day_of_week": a.day_of_week,
                    "start_time": getattr(a, "start_time", None),
                    "end_time": getattr(a, "end_time", None),
                }
                for a in worker.availabilities
            ],
        })

    return response




