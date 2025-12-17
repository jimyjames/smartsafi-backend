from fastapi import APIRouter
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import base64
import stripe
import os
from sqlalchemy.orm import Session
from models import Booking, Payment

def lipa_na_mpesa_online(phone: str ="254759234753", amount: float= 1.0):
    # Step 1: Get access token
    consumer_key = os.getenv("Mpesa_Consumer_Key")
    consumer_secret = os.getenv("Mpesa_Consumer_Secret")
    auth_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    
    auth_response = requests.get(auth_url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    access_token = auth_response.json()["access_token"]

    # Step 2: Prepare STK Push payload
    shortcode = "174379"
    # phone="254790329962"
    passkey = os.getenv("Mpesa_Passkey")
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    
    password = base64.b64encode((shortcode + passkey + timestamp).encode()).decode()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        # "PartyA": "254759234753",  # customer's phone number
        "PartyA": phone,
        "PartyB": shortcode,
        # "PhoneNumber": "254759234753",  # same as PartyA
        "PhoneNumber": phone,
        "CallBackURL": "https://yourdomain.com/callback",
        "AccountReference": "Test123",
        "TransactionDesc": "Payment for goods"
    }
    print("as received" , phone, amount)
    response = requests.post(
        "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
        headers=headers,
        json=payload
    )

    return response.json()


def stripe_payment_test(amount: float= 100.0, currency: str ="usd", source: str ="tok_visa"):
    stripe.api_key = os.getenv("stripe_api_key")

    try:
        charge = stripe.Charge.create(
            amount=int(amount * 100),  # Amount in cents
            currency=currency,
            source=source,
            description="Test Charge"
        )
        return charge
    except stripe.error.StripeError as e:
        return {"error": str(e)}


def deposit_payment_intent(booking_id: int, db: Session):
    booking = db.query(Booking).get(booking_id)

    deposit_amount = booking.total_price * 0.15

    intent = stripe.PaymentIntent.create(
        amount=int(deposit_amount * 100),
        currency="usd",
        metadata={
            "booking_id": booking.id,
            "payment_type": "deposit",
        },
    )

    payment = Payment(
        booking_id=booking.id,
        amount=deposit_amount,
        type="deposit",
        status="pending",
        stripe_payment_intent_id=intent.id,
    )

    db.add(payment)
    db.commit()

    return intent



router = APIRouter(prefix="/payments", tags=["payments"])