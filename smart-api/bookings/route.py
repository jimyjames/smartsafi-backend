from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session,joinedload
from schemas import  BookingCreate, BookingResponse,BookingServiceResponse,BookingServiceCreate
from models import Booking,Client,FeatureOption,BookingService,ServiceFeature, ServiceCategory
from payments.route import lipa_na_mpesa_online
from database import get_db

booking_router = APIRouter(prefix="/bookings", tags=["bookings"])


# @booking_router.get("/", response_model=list[BookingOut])
# def get_bookings(db: Session = Depends(get_db)):
#     bookings = db.query(Booking).all()
#     return bookings

# @booking_router.get("/{booking_id}", response_model=BookingOut)
# def get_booking(booking_id: int, db: Session = Depends(get_db)):
#     booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
#     if not booking:
#         raise HTTPException(status_code=404, detail="Booking not found")
#     return booking  

# @booking_router.get("/client/{client_id}", response_model=list[BookingOut])
# def get_bookings_by_client(client_id: int, db: Session = Depends(get_db)):
#     bookings = db.query(Booking).filter(Booking.client_id == client_id).all()
#     if not bookings:
#         raise HTTPException(status_code=404, detail="No bookings found for this client")
#     return bookings

# @booking_router.post("/", response_model=BookingOut)
# def create_booking(booking: BookingBase, db: Session = Depends(get_db)):
#     db_booking = Booking(**booking.dict())
#     db.add(db_booking)
#     db.commit()
#     db.refresh(db_booking)
#     # QUERY phone number for client
#     phone_number = db.query(Client.phone_number).filter(Client.client_id == booking.client_id).first()
#     print(phone_number)
#     if not phone_number:
    
#         raise HTTPException(status_code=404, detail="Client phone numbernot found")
#     # Process payment using the phone number and booking total price
#     try:
#         lipa_na_mpesa_online(phone=phone_number[0], amount=booking.total_price)
#         return db_booking
#     except Exception as e:
#     # Assuming this function handles payment
#         raise HTTPException(status_code=500, detail=f"Payment processing failed: {str(e)}")
    
    


@booking_router.post("/", response_model=BookingResponse)
def create_booking(booking_data: BookingCreate, db: Session = Depends(get_db)):
    # Create the booking
    new_booking = Booking(
        client_id=booking_data.client_id,
        worker_id=booking_data.worker_id,
        appointment_datetime=booking_data.appointment_datetime,
        service_feature_id=booking_data.service_feature_id,
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


@booking_router.get("/{client_id}", response_model=list[BookingResponse])
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

@booking_router.get("/stk/" )
def get_stk_info():
    return lipa_na_mpesa_online(phone="254759234753", amount="10")