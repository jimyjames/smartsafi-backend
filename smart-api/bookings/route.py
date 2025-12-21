import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session,joinedload
from sqlalchemy import func
from schemas import  BookingCreate, BookingResponse, BookingRequestCreate,BookingRequestUpdate,BookingRequestResponse,BookingUpdate,BookingBase,WorkerRatingBase
from models import Booking,Client,FeatureOption,BookingService,ServiceFeature, BookingRequest,Workers, Notification
from payments.route import lipa_na_mpesa_online,create_deposit_payment_intent
from payments import deposit_payment_intent
from database import get_db
from typing import List, Optional

booking_router = APIRouter(prefix="/bookings", tags=["bookings"]) 
jobs_router = APIRouter(prefix="/jobs", tags=["jobs"])


# @booking_router.post("/", response_model=BookingResponse)
# def create_booking(booking_data: BookingCreate, db: Session = Depends(get_db)):
#     # Create the booking
#     new_booking = Booking(
#         client_id=booking_data.client_id,
#         worker_id=booking_data.worker_id,
#         appointment_datetime=booking_data.appointment_datetime,
#         service_feature_id=booking_data.service_feature_id,
#         location=booking_data.location,
#         description=booking_data.description,
#         total_price=booking_data.total_price,
#         deposit_paid=False,
#         status=booking_data.status,
#         rating=booking_data.rating,
#         # special_requests=booking_data.special_requests,
#         # preferred_language=booking_data.preferred_language

#     )

#     client_exists = db.query(Client).filter(Client.id == booking_data.client_id).first()
#     if not client_exists:
#         raise HTTPException(status_code=404, detail="Client not found")
#     worker_exists = db.query(Client).filter(Client.id == booking_data.worker_id).first()
#     if booking_data.worker_id and not worker_exists:
#         raise HTTPException(status_code=404, detail="Worker not found")

#     db.add(new_booking)
#     db.commit()  # So we get booking.id

#     # Add booked services
#     for service in booking_data.booked_services:
#         # Optional: validate the feature_option exists
#         option = db.query(FeatureOption).filter(FeatureOption.id == service.feature_option_id).first()
#         if not option:
#             raise HTTPException(status_code=404, detail=f"Feature option {service.feature_option_id} not found")

#         booking_service = BookingService(
#             booking_id=new_booking.id,
#             feature_option_id=service.feature_option_id,
#             quantity=service.quantity,
#             unit_price=service.unit_price,
#             total_price=service.total_price
#         )
#         db.add(booking_service)

#     db.commit()

#     booking_id_exists = db.query(Booking).filter(Booking.id == new_booking.id).first()

#     if worker_exists and booking_id_exists:
#         notification = Notification(
#             user_id=worker_exists.user_id,   # IMPORTANT: user_id, not worker_exists.id
#             title="New Booking Request",
#             message=(
#                 f"You have a new booking scheduled for "
#                 f"{new_booking.appointment_datetime.strftime('%d %b %Y, %I:%M %p')}."
#             ),
#             is_read=False,
#             created_at=datetime.utcnow(),
#         )
#         db.add(notification)


#         #########initiate eposit payment request here ##########
#         deposit_payment_intent(booking_id=new_booking.id, db=db)


    
    
#     db.refresh(new_booking)
#     return new_booking


@booking_router.post("/", response_model=BookingResponse)
def create_booking(
    booking_data: BookingCreate,
    db: Session = Depends(get_db)
):
    # Validate client
    client = db.query(Client).filter(Client.id == booking_data.client_id).first()
    if not client:
        raise HTTPException(404, "Client not found")

    # Validate worker
    worker = db.query(Workers).filter(Workers.id == booking_data.worker_id).first()
    if not worker:
        raise HTTPException(404, "Worker not found")

    # Create booking
    new_booking = Booking(
        client_id=booking_data.client_id,
        worker_id=booking_data.worker_id,
        appointment_datetime=booking_data.appointment_datetime,
        service_feature_id=booking_data.service_feature_id,
        location=booking_data.location,
        description=booking_data.description,
        total_price=booking_data.total_price,
        deposit_paid=False,
        status="pending_payment",
    )

    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    # Add booked services
    for service in booking_data.booked_services:
        option = db.query(FeatureOption).filter(
            FeatureOption.id == service.feature_option_id
        ).first()

        if not option:
            raise HTTPException(
                404, f"Feature option {service.feature_option_id} not found"
            )

        db.add(
            BookingService(
                booking_id=new_booking.id,
                feature_option_id=service.feature_option_id,
                quantity=service.quantity,
                unit_price=service.unit_price,
                total_price=service.total_price,
            )
        )

    db.commit()

    # Create notification for worker
    notification = Notification(
        user_id=worker.user_id,
        title="New Booking Request",
        message=(
            f"You have a new booking scheduled for "
            f"{new_booking.appointment_datetime.strftime('%d %b %Y, %I:%M %p')}"
        ),
        is_read=False,
    )
    db.add(notification)
    db.commit()

    # 🔑 Create Stripe deposit PaymentIntent
    payment_intent = create_deposit_payment_intent(
        booking_id=new_booking.id,
        db=db
    )

    return {
        **new_booking.__dict__,
        "stripe_client_secret": payment_intent
    }


@booking_router.get("/", response_model=list[BookingResponse])
def get_bookings(db: Session = Depends(get_db)):
    bookings = (
        db.query(Booking)
        .options(
            joinedload(Booking.client),
            joinedload(Booking.worker),
            joinedload(Booking.booked_services)
            .joinedload(BookingService.feature_option)
            .joinedload(FeatureOption.feature)
            .joinedload(ServiceFeature.category)  # ✅ loads category through feature
        )
        .all()
    )
    return bookings


@booking_router.get("/client/{client_id}", response_model=list[BookingResponse])
def get_bookings_by_client(client_id: int, db: Session = Depends(get_db)):
    client_exists = db.query("   Booking request created successfully",Client).filter(Client.id == client_id).first()
    if not client_exists:
        raise HTTPException(status_code=404, detail="Client not found")

    bookings = db.query(Booking).options(
        joinedload(Booking.client),
        joinedload(Booking.worker),
        joinedload(Booking.booked_services).joinedload(BookingService.feature_option)
    ).filter(Booking.client_id == client_id).all()

    if not bookings:
        raise HTTPException(status_code=404, detail="No bookings found for this client")

    return bookings

@booking_router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).options(
        joinedload(Booking.client),
        joinedload(Booking.worker),
        joinedload(Booking.booked_services).joinedload(BookingService.feature_option)
    ).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking

@booking_router.put("/{booking_id}", response_model=BookingResponse)
def update_booking(
    booking_id: int, request: BookingUpdate, db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    for key, value in request.dict(exclude_unset=True).items():
        setattr(booking, key, value)

    db.commit()
    db.refresh(booking)
    return booking


@booking_router.get("/stk/" )
def get_stk_info():
    return lipa_na_mpesa_online(phone="254759234753", amount="10")

@booking_router.post("/requests/", response_model=BookingRequestResponse)
def create_booking_request(request: BookingRequestCreate, db: Session = Depends(get_db)):
    print("Creating booking request with data:", request.dict())
    booking = BookingRequest(**request.dict())
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return (booking)


# # ✅ Get all Booking Requests
# @booking_router.get("/requests/", response_model=List[BookingRequestResponse])
# def get_all_booking_requests(db: Session = Depends(get_db)):
#     return db.query(BookingRequest).all()


# # ✅ Get Booking Request by ID
# @booking_router.get("/requests/{booking_id}", response_model=BookingRequestResponse)
# def get_booking_request(booking_id: int, db: Session = Depends(get_db)):
#     booking = db.query(BookingRequest).filter(BookingRequest.id == booking_id).first()
#     if not booking:
#         raise HTTPException(status_code=404, detail="Booking request not found")
#     return booking

@booking_router.get("/requests/client/{client_id}", response_model=List[BookingRequestResponse])
def get_booking_requests_by_client(client_id: int, db: Session = Depends(get_db)):
    client_exists = db.query(Client).filter(Client.id == client_id).first()
    if not client_exists:
        raise HTTPException(status_code=404, detail="Client not found")
    booking_requests_exists = db.query(BookingRequest).filter(BookingRequest.client_id == client_id).all()
    if not booking_requests_exists:
        raise HTTPException(status_code=404, detail="No booking requests found for this client")

    return booking_requests_exists


# ✅ Update Booking Request
@booking_router.put("/requests/{booking_id}", response_model=BookingRequestResponse)
def update_booking_request(
    booking_id: int, request: BookingRequestUpdate, db: Session = Depends(get_db)
):
    booking = db.query(BookingRequest).filter(BookingRequest.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking request not found")

    for key, value in request.dict(exclude_unset=True).items():
        setattr(booking, key, value)

    db.commit()
    db.refresh(booking)
    return booking


from sqlalchemy.orm import joinedload

# ✅ Get all booking requests
@booking_router.get("/requests/", response_model=List[BookingRequestResponse])
def get_all_booking_requests(db: Session = Depends(get_db)):
    return (
        db.query(BookingRequest)
        .options(
            joinedload(BookingRequest.client),
            joinedload(BookingRequest.worker),
            joinedload(BookingRequest.feature).joinedload(ServiceFeature.category)
        )
        .all()
    )

# ✅ Get booking request by ID
@booking_router.get("/requests/{booking_id}", response_model=BookingRequestResponse)
def get_booking_request(booking_id: int, db: Session = Depends(get_db)):
    booking = (
        db.query(BookingRequest)
        .options(
            joinedload(BookingRequest.client),
            joinedload(BookingRequest.worker),
            joinedload(BookingRequest.feature).joinedload(ServiceFeature.category)
        )
        .filter(BookingRequest.id == booking_id)
        .first()
    )
    if not booking:
        raise HTTPException(status_code=404, detail="Booking request not found")
    return booking


# ✅ Delete Booking Request
@booking_router.delete("/requests/{booking_id}")
def delete_booking_request(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(BookingRequest).filter(BookingRequest.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking request not found")

    db.delete(booking)
    db.commit()
    return {"detail": "Booking request deleted"}


#### from here on we have routes to obtain bookings but from a workers perspective ####



#### ge all workers bookings and categorize them based on their status ####

def get_worker_bookings(worker_id: int, db: Session = Depends(get_db)):
    # 1. Verify worker exists
    worker_exists = db.query(Workers).filter(Workers.id == worker_id).first()
    if not worker_exists:
        raise HTTPException(status_code=404, detail="Worker not found")

    # 2. Fetch all worker bookings with joins
    bookings = db.query(Booking).options(
        joinedload(Booking.client),
        joinedload(Booking.worker),
        joinedload(Booking.booked_services).joinedload(BookingService.feature_option)
    ).filter(Booking.worker_id == worker_id).all()

    # 3. Group the bookings by status
    grouped = {
        "pending": [],
        "accepted": [],
        "in_progress": [],
        "completed": [],
        "cancelled": []
    }

    for booking in bookings:
        grouped[booking.status].append(booking) 
    return grouped
def get_worker_job_counts( worker_id: int,db: Session = Depends(get_db)):
    results = (
        db.query(Booking.status, func.count(Booking.id))
        .filter(Booking.worker_id == worker_id)
        .group_by(Booking.status)
        .all()
    )

    # default values
    counts = {
        "pending": 0,
        "accepted": 0,
        "in_progress": 0,
        "completed": 0,
        "cancelled": 0,
    }

    # fill real values
    for status, count in results:
        counts[status] = count

    return counts


###### create a review for a completed job ######
@jobs_router.put("/{booking_id}/review", response_model=BookingResponse)
def add_review_to_booking(
    booking_id: int,
    review_data: WorkerRatingBase,
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.status != "completed":
        raise HTTPException(status_code=400, detail="Can only review completed bookings")

    booking.rating = review_data.rating
    booking.review = review_data.review

    db.commit()
    db.refresh(booking)
    return booking

