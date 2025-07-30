from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from schemas import BookingBase,BookingOut,BookingPayment
from models import Booking,Client
from payments.route import lipa_na_mpesa_online
from database import get_db

booking_router = APIRouter(prefix="/bookings", tags=["bookings"])


@booking_router.get("/", response_model=list[BookingOut])
def get_bookings(db: Session = Depends(get_db)):
    bookings = db.query(Booking).all()
    return bookings

@booking_router.get("/{booking_id}", response_model=BookingOut)
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking  

@booking_router.get("/client/{client_id}", response_model=list[BookingOut])
def get_bookings_by_client(client_id: int, db: Session = Depends(get_db)):
    bookings = db.query(Booking).filter(Booking.client_id == client_id).all()
    if not bookings:
        raise HTTPException(status_code=404, detail="No bookings found for this client")
    return bookings

@booking_router.post("/", response_model=BookingOut)
def create_booking(booking: BookingBase, db: Session = Depends(get_db)):
    db_booking = Booking(**booking.dict())
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    # QUERY phone number for client
    phone_number = db.query(Client.phone_number).filter(Client.client_id == booking.client_id).first()
    print(phone_number)
    if not phone_number:
    
        raise HTTPException(status_code=404, detail="Client phone numbernot found")
    # Process payment using the phone number and booking total price
    try:
        lipa_na_mpesa_online(phone=phone_number[0], amount=booking.total_price)
        return db_booking
    except Exception as e:
    # Assuming this function handles payment
        raise HTTPException(status_code=500, detail=f"Payment processing failed: {str(e)}")
    
    
@booking_router.get("/stk/" )
def get_stk_info():
    return lipa_na_mpesa_online(phone="254759234753", amount="10")