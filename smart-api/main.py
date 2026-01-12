import datetime
from fastapi import FastAPI
from database import  engine
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import models

from  users import route as users_route
from bookings import route as bookings_router
# from booking
from authentication.route import auth_router
from clients.route import router as clients_router
from workers.route import router as worker_router
# from Services.route import service_router
from Services.route import router as service_router
from Services.route import router as s_route
from payments.route import paymentsrouter
from notifications.route import router as notifications_router
from wallet.route import router as wallet_router
from messages.route import router as messages_router
# from admin import router as admin_router
from admin.route import router as admin_router
from admin.hr_admin import router as hr_admin_router
# Create DB tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart Safi API",
    description="API for Smart Safi Application",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")



app.include_router(users_route.users_router)
app.include_router(bookings_router.booking_router)
app.include_router(auth_router)
app.include_router(clients_router)
app.include_router(worker_router)
app.include_router(service_router)
app.include_router(paymentsrouter)
app.include_router(s_route)
app.include_router(notifications_router)
app.include_router(wallet_router)
app.include_router(admin_router)
app.include_router(messages_router)
app.include_router(hr_admin_router)

@app.get("/")
def root():
    return {
        "message": "Service Platform API",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/auth",
            "admin": "/admin",
            "hr": "/hr",
            "workers": "/workers",
            "clients": "/clients"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}