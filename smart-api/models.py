
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
    notifications = relationship("Notification", back_populates="user")


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
    






class Language(Base):
    __tablename__ = "languages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    # optionally, backref to bookings
    bookings = relationship("Booking", back_populates="preferred_language")
    workers_languages = relationship("WorkerLanguages", back_populates="language", cascade="all, delete")

class WorkerTypeEnum(str, enum.Enum):
    individual = "individual"
    organization = "organization"


class Workers(Base):
    __tablename__ = "workers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    public_id = Column(String(100), unique=True, default=lambda: "Wr" + str(uuid4()))
    worker_type = Column(String, nullable=False, default=WorkerTypeEnum.individual.value)
    organization_id = Column(Integer, ForeignKey("workers.id"), nullable=True)  

    # Personal Info
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    organization_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=False)
    address = Column(Text, nullable=True)
    profile_picture = Column(String, nullable=True)

    # Vetting & Compliance
    national_id_number = Column(String, nullable=False)
    # national_id_proof = Column(String, nullable=True)
    national_id_front = Column(String, nullable=True)
    national_id_back = Column(String, nullable=True)

    verification_id = Column(Boolean, default=False)

    good_conduct_number = Column(String, nullable=True)
    good_conduct_proof = Column(String, nullable=True)
    good_conduct_issue_date = Column(DateTime, nullable=True)
    good_conduct_expiry_date = Column(DateTime, nullable=True)
    verification_good_conduct = Column(Boolean, default=False)
    location_pin = Column(String, nullable=True)
    preferred_language_id = Column(Integer, ForeignKey("languages.id"), nullable=True)

    agreement_accepted = Column(Boolean, default=False)

    # Summary / Computed Stats
    average_rating = Column(Float, default=0.0)
    jobs_completed = Column(Integer, default=0)

    # Financial & Communication
    mpesa_number = Column(String, nullable=False)
    bank_name = Column(String, nullable=True)
    bank_account_name = Column(String, nullable=True)
    bank_account_number = Column(String, nullable=True)

    notifications_enabled = Column(Boolean, default=True)
    chat_enabled = Column(Boolean, default=True)
    chat_policy_accepted = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="worker")
    assigned_bookings = relationship("Booking", back_populates="worker")
    assigned_booking_requests = relationship("BookingRequest", back_populates="worker")

    # New relations
    emergency_contacts = relationship("WorkerEmergencyContact", back_populates="worker", cascade="all, delete")
    equipments = relationship("WorkerEquipment", back_populates="worker", cascade="all, delete")
    services = relationship("WorkerService", back_populates="worker", cascade="all, delete")
    availabilities = relationship("WorkerAvailability", back_populates="worker", cascade="all, delete")
    ratings = relationship("WorkerRating", back_populates="worker", cascade="all, delete")
    languages = relationship("WorkerLanguages", back_populates="worker", cascade="all, delete")



class WorkerEmergencyContact(Base):
    __tablename__ = "worker_emergency_contacts"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False)
    name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    relationship_to_worker = Column(String, nullable=True)

    worker = relationship("Workers", back_populates="emergency_contacts")

class WorkerEquipment(Base):
    __tablename__ = "worker_equipment"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False)
    equipment_name = Column(String, nullable=False)   # e.g., "vacuum cleaner"
    has_equipment = Column(Boolean, default=True)
    equipment_image = Column(String, nullable=True)  # store path/URL to image
    equipment_description = Column(String, nullable=True)
    equipment_status = Column(String, nullable=True)  # e.g., "working", "needs repair"

    worker = relationship("Workers", back_populates="equipments")


class WorkerService(Base):
    __tablename__ = "worker_services"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("service_categories.id"), nullable=False)
    experience_years = Column(Integer, default=0)

    worker = relationship("Workers", back_populates="services")
    category = relationship("ServiceCategory")


class WorkerAvailability(Base):
    __tablename__ = "worker_availability"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False)

    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = Column(String, nullable=False, default="06:00")    # e.g. "08:00"
    end_time = Column(String, nullable=False, default="18:00")      # e.g. "17:00"

    worker = relationship("Workers", back_populates="availabilities")


class WorkerRating(Base):
    __tablename__ = "worker_ratings"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)

    rating = Column(Float, nullable=False)   # 1–5 stars
    review = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    worker = relationship("Workers", back_populates="ratings")
    booking = relationship("Booking")


class WorkerLanguages(Base):
    __tablename__ = "worker_languages"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False)
    language_id = Column(Integer, ForeignKey("languages.id"), nullable=False)

    worker = relationship("Workers", back_populates="languages")
    language = relationship("Language", back_populates="workers_languages")


class WorkerPayments(Base):
    __tablename__ = "worker_payments"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime, default=datetime.utcnow)
    payment_method = Column(String, nullable=False)  # e.g., "mpesa", "bank_transfer"
    paid_by = Column(String, nullable=True)
    payment_reference = Column(String, nullable=True)
    work_done = Column(Integer, ForeignKey("bookings.id"), nullable=False)

    reference_number = Column(String, nullable=True)

    worker = relationship("Workers")
    booking_jobs = relationship("Booking")
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
    description=Column(String)
    location = Column(String,nullable=False)

    date_of_booking = Column(DateTime, default=datetime.utcnow)
    appointment_datetime = Column(DateTime, nullable=False)

    service_feature_id = Column(Integer, ForeignKey("service_features.id"), nullable=False)

    total_price = Column(Float, nullable=False)
    deposit_paid = Column(Float, default=0.0)
    # deposit_payment = Column(Integer, ForeignKey("worker_payments.id"), nullable=True)
    # balance_payment = Column(Integer, ForeignKey("worker_payments.id"), nullable=True)
    status = Column(String, default="pending", nullable=False)  # could use PaymentStatusEnum
    rating = Column(Float, nullable=True)  # optional customer rating
    review = Column(Text, nullable=True)  # optional customer review
    preferred_worker_language = Column(Integer, ForeignKey('languages.id'), nullable=True)
    special_requests = Column(Text, nullable=True)


    # deposit_payment = relationship("WorkerPayments", foreign_keys=[deposit_payment])
    # balance_payment = relationship("WorkerPayments", foreign_keys=[balance_payment])
    worker_payments = relationship("WorkerPayments", back_populates="booking_jobs")
    preferred_language = relationship("Language", back_populates="bookings")
    client = relationship("Client", backref="bookings")
    worker = relationship("Workers", back_populates="assigned_bookings")
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


class BookingRequest(Base):
    __tablename__ = "booking_requests"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String(100), unique=True, default=lambda: "BR" + str(uuid4()))

    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=True)

    service_feature_id = Column(Integer, ForeignKey("service_features.id"), nullable=False)

    requested_date = Column(DateTime, default=datetime.utcnow)
    appointment_datetime=Column(DateTime, nullable=False)
    location = Column(String, nullable=False)
    description = Column(String, nullable=True)
    pricing = Column(Float)
    status = Column(String, default="pending", nullable=False)

    client = relationship("Client", backref="booking_requests")
    worker = relationship("Workers", back_populates="assigned_booking_requests")
    feature = relationship("ServiceFeature", back_populates="booking_requests")



class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String(100), unique=True, default=lambda: "NT" + str(uuid4()))

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")



class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)  
    content = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)

    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])
    booking = relationship("Booking", backref="messages")


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
    booking_requests = relationship("BookingRequest", back_populates="feature", cascade="all, delete")

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