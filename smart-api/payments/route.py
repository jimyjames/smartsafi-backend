from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status
from . import lipa_na_mpesa_online,router, stripe_payment_test
from sqlalchemy.orm import Session
from schemas import ClientCreate, ClientOut, ClientBase
from models import Client, User
from database import SessionLocal, get_db
from pathlib import Path
import shutil,stripe
from models import Booking, Payment


paymentsrouter = router

@paymentsrouter.get("/stk", response_model=dict)
def get_stk_info():
    return lipa_na_mpesa_online()   

@paymentsrouter.get("/stripe", response_model=dict)
def test_stripe_payment():
    return stripe_payment_test()


@router.post("/create-intent/{booking_id}", response_model=dict)

def create_deposit_payment_intent(
    booking_id: int,
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(404, "Booking not found")

    deposit_amount = booking.total_amount * 0.15

    intent = stripe.PaymentIntent.create(
        amount=int(deposit_amount * 100),  # cents
        currency="usd",
        metadata={
            "booking_id": booking.id,
            "payment_type": "deposit"
        }
    )

    booking.deposit_amount = deposit_amount
    booking.remaining_amount = booking.total_amount - deposit_amount
    booking.stripe_payment_intent_id = intent.id

    payment = Payment(
        booking_id=booking.id,
        amount=deposit_amount,
        type="deposit",
        status="pending",
        stripe_payment_intent_id=intent.id
    )

    db.add(payment)
    db.commit()

    return {
        "clientSecret": intent.client_secret
    }


# @router.post("/webhooks/stripe")
# async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
#     payload = await request.body()
#     sig_header = request.headers.get("stripe-signature")

#     event = stripe.Webhook.construct_event(
#         payload,
#         sig_header,
#         settings.STRIPE_WEBHOOK_SECRET
#     )

#     if event["type"] == "payment_intent.succeeded":
#         intent = event["data"]["object"]

#         payment = (
#             db.query(Payment)
#             .filter(Payment.stripe_payment_intent_id == intent.id)
#             .first()
#         )

#         payment.status = "paid"

#         booking = db.query(Booking).get(payment.booking_id)

#         if payment.type == "deposit":
#             booking.status = "deposit_paid"
#         else:
#             booking.status = "completed"

#         db.commit()

#     return {"status": "ok"}
