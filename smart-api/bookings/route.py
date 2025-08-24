from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session,joinedload
from schemas import  BookingCreate, BookingResponse, BookingRequestCreate,BookingRequestUpdate,BookingRequestResponse
from models import Booking,Client,FeatureOption,BookingService,ServiceFeature, BookingRequest
from payments.route import lipa_na_mpesa_online
from database import get_db
from typing import List, Optional

booking_router = APIRouter(prefix="/bookings", tags=["bookings"]) 


@booking_router.post("/", response_model=BookingResponse)
def create_booking(booking_data: BookingCreate, db: Session = Depends(get_db)):
    # Create the booking
    new_booking = Booking(
        client_id=booking_data.client_id,
        worker_id=booking_data.worker_id,
        appointment_datetime=booking_data.appointment_datetime,
        service_feature_id=booking_data.service_feature_id,
        location=booking_data.location,
        description=booking_data.description,
        total_price=booking_data.total_price,
        deposit_paid=booking_data.deposit_paid,
        status=booking_data.status,
        rating=booking_data.rating
    )

    client_exists = db.query(Client).filter(Client.id == booking_data.client_id).first()
    if not client_exists:
        raise HTTPException(status_code=404, detail="Client not found")
    worker_exists = db.query(Client).filter(Client.id == booking_data.worker_id).first()
    if booking_data.worker_id and not worker_exists:
        raise HTTPException(status_code=404, detail="Worker not found")

    db.add(new_booking)
    db.commit()  # So we get booking.id

    # Add booked services
    for service in booking_data.booked_services:
        # Optional: validate the feature_option exists
        option = db.query(FeatureOption).filter(FeatureOption.id == service.feature_option_id).first()
        if not option:
            raise HTTPException(status_code=404, detail=f"Feature option {service.feature_option_id} not found")

        booking_service = BookingService(
            booking_id=new_booking.id,
            feature_option_id=service.feature_option_id,
            quantity=service.quantity,
            unit_price=service.unit_price,
            total_price=service.total_price
        )
        db.add(booking_service)

    db.commit()
    db.refresh(new_booking)
    return new_booking


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
    client_exists = db.query(Client).filter(Client.id == client_id).first()
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
def update_booking_request(
    booking_id: int, request: BookingRequestUpdate, db: Session = Depends(get_db)
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
    booking = BookingRequest(**request.dict())
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


# ✅ Get all Booking Requests
@booking_router.get("/requests/", response_model=List[BookingRequestResponse])
def get_all_booking_requests(db: Session = Depends(get_db)):
    return db.query(BookingRequest).all()


# ✅ Get Booking Request by ID
@booking_router.get("/requests/{booking_id}", response_model=BookingRequestResponse)
def get_booking_request(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(BookingRequest).filter(BookingRequest.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking request not found")
    return booking

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


# ✅ Delete Booking Request
@booking_router.delete("/requests/{booking_id}")
def delete_booking_request(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(BookingRequest).filter(BookingRequest.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking request not found")

    db.delete(booking)
    db.commit()
    return {"detail": "Booking request deleted"}