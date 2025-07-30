
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

    client_id = Column(Integer, primary_key=True, index=True)
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

    worker_id = Column(Integer, primary_key=True, index=True)
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
class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String(100), unique=True, default=lambda: "Bk" + str(uuid4()))

    client_id = Column(Integer, ForeignKey("clients.client_id"), nullable=False)
    worker_id = Column(Integer, ForeignKey("workers.worker_id"), nullable=True)

    service_name = Column(String, nullable=False, default="Premium Deep Cleaning")
    description = Column(Text, nullable=True)

    property_type = Column(String, nullable=False)
    bedrooms = Column(Integer, default=0)
    instructions = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    booking_date = Column(DateTime, default=datetime.utcnow)
    scheduled_time = Column(DateTime, nullable=False)

    location_pin = Column(String, nullable=False)

    total_price = Column(Float, nullable=False)
    deposit_paid = Column(Float, default=0.0)
    payment_status = Column(String, default="pending", nullable=False)

    is_online_service = Column(Boolean, default=False)

    # Relationships
    client = relationship("Client", backref="bookings")
    worker = relationship("Workers", backref="assigned_bookings")


class ServiceName(Base):
    __tablename__ = "service_names"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    descriptions = relationship("ServiceDescription", back_populates="service_name")



class ServiceDescription(Base):
    __tablename__ = "service_descriptions"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    icon = Column(String , nullable=True)

    service_name_id = Column(Integer, ForeignKey("service_names.id"))
    service_name = relationship("ServiceName", back_populates="descriptions")

    features = relationship("ServiceFeature", back_populates="service_description")


class ServiceFeature(Base):
    __tablename__ = "service_features"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    icon = Column(String)

    service_description_id = Column(Integer, ForeignKey("service_descriptions.id"))
    service_description = relationship("ServiceDescription", back_populates="features")

    prices = relationship("ServicePrice", back_populates="service_feature", cascade="all, delete-orphan")

# class ServiceFeature(Base):
#     __tablename__ = "service_features"

#     id = Column(Integer, primary_key=True)
#     name = Column(String, nullable=False)
#     icon = Column(String)

#     service_description_id = Column(Integer, ForeignKey("service_descriptions.id"))
#     service_description = relationship("ServiceDescription", back_populates="features")

#     prices = relationship("ServicePrice",
#                         #    lazy="dynamic",
#                              cascade="all,delete-orphan",back_populates="service_feature")


class ServicePrice(Base):
    __tablename__ = "service_prices"

    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    unit = Column(String, default="KES")

    service_feature_id = Column(Integer, ForeignKey("service_features.id"))
    service_description_id = Column(Integer, ForeignKey("service_descriptions.id"))

    service_feature = relationship("ServiceFeature", back_populates="prices")
    service_description = relationship("ServiceDescription")

    __table_args__ = (
        UniqueConstraint('service_feature_id', 'service_description_id', name='unique_feature_per_description'),
    )


# class ServicePrice(Base):
#     __tablename__ = "service_prices"

#     id = Column(Integer, primary_key=True)
#     amount = Column(Float, nullable=False)
#     unit = Column(String, default="KES")  # or e.g., "per room", "per item"

#     service_feature_id = Column(Integer, ForeignKey("service_features.id"))
#     service_description_id = Column(Integer, ForeignKey("service_descriptions.id"))

#     __table_args__ = (
#         UniqueConstraint('service_feature_id', 'service_description_id', name='unique_feature_per_description'),
#     )

#     service_feature = relationship("ServiceFeature", back_populates="prices")
#     service_description = relationship("ServiceDescription")

