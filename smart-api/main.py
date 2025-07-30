from fastapi import FastAPI
from database import  engine
import models
from fastapi.middleware.cors import CORSMiddleware
from  users import route as users_route
from bookings import route as bookings_router
from authentication.route import auth_router
from clients.route import router as clients_router
from workers.route import router as worker_router
from Services.route import service_router
from payments.route import paymentsrouter
# Create DB tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)





app.include_router(users_route.users_router)
app.include_router(bookings_router.booking_router)
app.include_router(auth_router)
app.include_router(clients_router)
app.include_router(worker_router)
app.include_router(service_router)
app.include_router(paymentsrouter)