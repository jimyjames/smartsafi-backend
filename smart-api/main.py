from fastapi import FastAPI
from database import  engine
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import models

from  users import route as users_route
from bookings import route as bookings_router
from authentication.route import auth_router
from clients.route import router as clients_router
from workers.route import router as worker_router
# from Services.route import service_router
from Services.route import router as service_router
from Services.route import router as s_route
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




app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")



app.include_router(users_route.users_router)
app.include_router(bookings_router.booking_router)
app.include_router(auth_router)
app.include_router(clients_router)
app.include_router(worker_router)
app.include_router(service_router)
app.include_router(paymentsrouter)
app.include_router(s_route)