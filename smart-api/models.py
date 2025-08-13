
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Enum, DateTime, Float, UniqueConstraint
from sqlalchemy.orm import relationship
import enum
from uuid import uuid4
from database import Base
from datetime import datetime



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    public_user_id = Column(
        String(100), unique=True, default=lambda: "USR" + str(uuid4())
    )
    is_admin = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)

    client = relationship("Client", back_populates="user", uselist=False)
    worker = relationship("Workers", back_populates="user", uselist=False)


class ClientTypeEnum(str, enum.Enum):
    individual = "individual"
    organization = "organization"




class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    public_id = Column(
        String(100), unique=True, default=lambda: "Cl" + str(uuid4())
    )

    client_type = Column(String, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    organization_name = Column(String, nullable=True)
    tax_number = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    tax_document_proof = Column(String, nullable=True)
    national_id_number = Column(Integer, nullable=True)
    national_id_proof = Column(String, nullable=True)
    verification_id = Column(Boolean, default=False)
    verification_tax = Column(Boolean, default=False)

    profile_picture = Column(String, nullable=True)

    user = relationship("User", back_populates="client")





class Workers(Base):
    __tablename__ = "workers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    public_id = Column(
        String(100), unique=True, default=lambda: "Wr" + str(uuid4())
    )

    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    address = Column(Text, nullable=True)
    good_conduct_proof = Column(String, nullable=True)
    national_id_number = Column(Integer, nullable=True)
    national_id_proof = Column(String, nullable=True)
    verification_id = Column(Boolean, default=False)
    verification_good_conduct = Column(Boolean, default=False)

    profile_picture = Column(String, nullable=True)

    user = relationship("User", back_populates="worker")



# Existing Enums


class PropertyTypeEnum(str, enum.Enum):
    apartment = "apartment"
    villa = "villa"
    studio = "studio"
    furnished = "furnished"
    unfurnished = "unfurnished"

# Booking Status Enum
class PaymentStatusEnum(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    partial = "partial"
    cancelled = "cancelled"

# Booking Model
# class Booking(Base):
#     __tablename__ = "bookings"

#     id = Column(Integer, primary_key=True, index=True)
#     public_id = Column(String(100), unique=True, default=lambda: "Bk" + str(uuid4()))

#     client_id = Column(Integer, ForeignKey("clients.client_id"), nullable=False)
#     worker_id = Column(Integer, ForeignKey("workers.worker_id"), nullable=True)

#     service_name = Column(String, nullable=False, default="Premium Deep Cleaning")
#     description = Column(Text, nullable=True)

#     property_type = Column(String, nullable=False)
#     bedrooms = Column(Integer, default=0)
#     instructions = Column(Text, nullable=True)
#     created_at = Column(DateTime, default=datetime.utcnow)
#     updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

#     booking_date = Column(DateTime, default=datetime.utcnow)
#     scheduled_time = Column(DateTime, nullable=False)

#     location_pin = Column(String, nullable=False)

#     total_price = Column(Float, nullable=False)
#     deposit_paid = Column(Float, default=0.0)
#     payment_status = Column(String, default="pending", nullable=False)

#     is_online_service = Column(Boolean, default=False)

#     # Relationships
#     client = relationship("Client", backref="bookings")
#     worker = relationship("Workers", backref="assigned_bookings")

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String(100), unique=True, default=lambda: "BK" + str(uuid4()))

    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=True)

    date_of_booking = Column(DateTime, default=datetime.utcnow)
    appointment_datetime = Column(DateTime, nullable=False)

    service_feature_id = Column(Integer, ForeignKey("service_features.id"), nullable=False)

    total_price = Column(Float, nullable=False)
    deposit_paid = Column(Float, default=0.0)
    status = Column(String, default="pending", nullable=False)  # could use PaymentStatusEnum
    rating = Column(Float, nullable=True)  # optional customer rating

    client = relationship("Client", backref="bookings")
    worker = relationship("Workers", backref="assigned_bookings")
    feature = relationship("ServiceFeature", back_populates="bookings")
    booked_services = relationship("BookingService", back_populates="booking", cascade="all, delete")


class BookingService(Base):
    __tablename__ = "booking_services"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    feature_option_id = Column(Integer, ForeignKey("feature_options.id"), nullable=False)

    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)  # quantity * unit_price

    booking = relationship("Booking", back_populates="booked_services")
    feature_option = relationship("FeatureOption")




class ServiceCategory(Base):
    __tablename__ = "service_categories"
    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String(100), unique=True, default=lambda: "SC" + str(uuid4()))
    slug = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    icon_name = Column(String)

    features = relationship("ServiceFeature", back_populates="category", cascade="all, delete")


class ServiceFeature(Base):
    __tablename__ = "service_features"
    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String(100), unique=True, default=lambda: "SF" + str(uuid4()))
    slug = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    icon_name = Column(String)
    category_id = Column(Integer, ForeignKey("service_categories.id"))

    category = relationship("ServiceCategory", back_populates="features")
    options = relationship("FeatureOption", back_populates="feature", cascade="all, delete")
    bookings = relationship("Booking", back_populates="feature", cascade="all, delete")

class FeatureOption(Base):
    __tablename__ = "feature_options"
    id = Column(Integer, primary_key=True, index=True)

    public_id = Column(String(100), unique=True, default=lambda: "FO" + str(uuid4()))
    feature_id = Column(Integer, ForeignKey("service_features.id"))
    area_type = Column(String, nullable=False)  # e.g. bedroom, kitchen
    label = Column(String, nullable=False)
    unit_price = Column(Float, nullable=False)
    min_units = Column(Integer, default=0)
    max_units = Column(Integer)

    feature = relationship("ServiceFeature", back_populates="options")