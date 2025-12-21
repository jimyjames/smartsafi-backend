from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status
from . import lipa_na_mpesa_online,router, stripe_payment_test
from sqlalchemy.orm import Session
from schemas import ClientCreate, ClientOut, ClientBase
from models import Client, User
from database import SessionLocal, get_db
from pathlib import Path
import os
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

    print("stripe secret key", os.getenv("stripe_api_key"))
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(404, "Booking not found")

    if booking.total_price is None:
        raise HTTPException(400, "Booking total price not set")

    # ✅ Check if a deposit payment already exists
    existing_payment = (
        db.query(Payment)
        .filter(
            Payment.booking_id == booking.id,
            Payment.type == "deposit",
            Payment.status.in_(["pending", "succeeded"])
        )
        .first()
    )

    if existing_payment:
        raise HTTPException(400, "Deposit payment already initiated")

    deposit_amount = booking.total_price * 0.15

    stripe.api_key = os.getenv("stripe_api_key")

    intent = stripe.PaymentIntent.create(
        amount=int(deposit_amount * 100),
        currency="usd",
        metadata={
            "booking_id": booking.id,
            "payment_type": "deposit"
        }
    )

    payment = Payment(
        booking_id=booking.id,
        amount=deposit_amount,
        currency="usd",
        type="deposit",
        status="pending",
        stripe_payment_intent=intent.id
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return {
        "clientSecret": intent
    }

# @router.post("/create-intent/{booking_id}", response_model=dict)

# # def create_deposit_payment_intent(
# #     booking_id: int,
# #     db: Session = Depends(get_db)
# # ):
# #     booking = db.query(Booking).filter(Booking.id == booking_id).first()
# #     if not booking:
# #         raise HTTPException(404, "Booking not found")

# #     deposit_amount = booking.total_price * 0.15

# #     intent = stripe.PaymentIntent.create(
# #         amount=int(deposit_amount * 100),  # cents
# #         currency="usd",
# #         metadata={
# #             "booking_id": booking.id,
# #             "payment_type": "deposit"
# #         }
# #     )

# #     booking.deposit_amount = deposit_amount
# #     booking.remaining_amount = booking.total_amount - deposit_amount
# #     booking.stripe_payment_intent_id = intent.id

# #     payment = Payment(
# #         booking_id=booking.id,
# #         amount=deposit_amount,
# #         type="deposit",
# #         status="pending",
# #         stripe_payment_intent_id=intent.id
# #     )

# #     db.add(payment)
# #     db.commit()

# #     return {
# #         "clientSecret": intent.client_secret
# #     }

# def create_deposit_payment_intent(
#     booking_id: int,
#     db: Session = Depends(get_db)
# ):
#     booking = db.query(Booking).filter(Booking.id == booking_id).first()
#     if not booking:
#         raise HTTPException(404, "Booking not found")

#     if booking.total_price is None:
#         raise HTTPException(400, "Booking total price not set")

#     if booking.stripe_payment_intent_id:
#         raise HTTPException(400, "Deposit payment already initiated")

#     deposit_amount = booking.total_price * 0.15

#     intent = stripe.PaymentIntent.create(
#         amount=int(deposit_amount * 100),
#         currency="usd",
#         metadata={
#             "booking_id": booking.id,
#             "payment_type": "deposit"
#         }
#     )

#     booking.deposit_amount = deposit_amount
#     booking.remaining_amount = booking.total_price - deposit_amount
#     booking.stripe_payment_intent_id = intent.id

#     payment = Payment(
#         booking_id=booking.id,
#         amount=deposit_amount,
#         type="deposit",
#         status="pending",
#         stripe_payment_intent_id=intent.id
#     )

#     db.add(booking)
#     db.add(payment)
#     db.commit()

#     return {
#         "clientSecret": intent.client_secret
#     }


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
