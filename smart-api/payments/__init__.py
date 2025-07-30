from fastapi import APIRouter
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import base64
import os

def lipa_na_mpesa_online(phone: str ="254759234753", amount: float= 1.0):
    # Step 1: Get access token
    consumer_key = "ZuTgM5j96tlERQBOq4ek6rw83CGEyxGV7W3MABQBfAFfI2Ck"
    consumer_secret = "pgTklUetHEWaCA88mbbAx5vZpUy2nCsjvIonIK6JsujOGqPHU6RRhaW5IvG8wjib"
    auth_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    
    auth_response = requests.get(auth_url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    access_token = auth_response.json()["access_token"]

    # Step 2: Prepare STK Push payload
    shortcode = "174379"
    # phone="254790329962"
    passkey = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
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



router = APIRouter(prefix="/payments", tags=["payments"])