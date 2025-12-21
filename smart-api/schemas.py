from pydantic import BaseModel, EmailStr, validator
from enum import Enum
from typing import Optional, List,Dict,Literal
from pydantic import BaseModel, field_validator,EmailStr
from datetime import datetime
from uuid import uuid4
from fastapi import Form, UploadFile, File

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str



# class ClientType(str, Enum):
#     individual = "individual"
#     organization = "organization"






class ClientBase (BaseModel):
 
    first_name: Optional[str]
    last_name: Optional[str]
    organization_name: Optional[str]
    tax_number: Optional[str]
    phone_number: Optional[str]
    national_id_number: Optional[int]
    address: Optional[str]
class ClientCreate(ClientBase):
    user_id: int
    client_type: Literal["individual", "organization"]
    national_id_number: Optional[int]
    verification_id: Optional[bool] = False
    verification_tax: Optional[bool] = False

    # @root_validator
    # def validate_fields(cls, values):
    #     ctype = values.get("client_type")
    #     if ctype == "individual" and (not values.get("first_name") or not values.get("last_name")):
    #         raise ValueError("first_name and last_name are required for individual clients.")
    #     if ctype == "organization" and (not values.get("organization_name") or not values.get("tax_number")):
    #         raise ValueError("organization_name and tax_number are required for organization clients.")
    #     return values

class ClientOut(ClientCreate):
    id: int
    national_id_proof:Optional[str]
    tax_document_proof:Optional[str]
    profile_picture:Optional[str]

    class Config:
        from_attributes = True


# ==========================
#  Language
# ==========================
class LanguageBase(BaseModel):
    name: str

class LanguageResponse(LanguageBase):
    id: int

    class Config:
        orm_mode = True


# ==========================
#  Worker Emergency Contact
# ==========================
class WorkerEmergencyContactBase(BaseModel):
    name: str
    phone_number: str
    relationship_to_worker: Optional[str] = None

class WorkerEmergencyContactCreate(WorkerEmergencyContactBase):
    pass

class WorkerEmergencyContactResponse(WorkerEmergencyContactBase):
    id: int

    class Config:
        orm_mode = True


# ==========================
#  Worker Equipment
# ==========================
class WorkerEquipmentBase(BaseModel):
    equipment_name: str
    has_equipment: bool = True
    equipment_image: Optional[str] = None
    equipment_description: Optional[str] = None
    equipment_status: Optional[str] = None



class WorkerEquipmentCreate:
    def __init__(
        self,
        equipment_name: str = Form(...),
        has_equipment: bool = Form(True),
        equipment_description: Optional[str] = Form(None),
        equipment_status: Optional[str] = Form(None),
        equipment_image: Optional[UploadFile] = File(None),
    ):
        self.equipment_name = equipment_name
        self.has_equipment = has_equipment
        self.equipment_description = equipment_description
        self.equipment_status = equipment_status
        self.equipment_image = equipment_image

class WorkerEquipmentResponse(WorkerEquipmentBase):
    id: int

    class Config:
        orm_mode = True


# ==========================
#  Worker Service
# ==========================
class WorkerServiceBase(BaseModel):
    category_id: int
    experience_years: int = 0

class WorkerServiceCreate(WorkerServiceBase):
    pass

class WorkerServiceResponse(WorkerServiceBase):
    id: int

    class Config:
        orm_mode = True


# ==========================
#  Worker Availability
# ==========================
class WorkerAvailabilityBase(BaseModel):
    day_of_week: str
    start_time: str
    end_time: str

class WorkerAvailabilityCreate(WorkerAvailabilityBase):
    pass

class WorkerAvailabilityResponse(WorkerAvailabilityBase):
    id: int

    class Config:
        orm_mode = True


# ==========================
#  Worker Rating
# ==========================
class WorkerRatingBase(BaseModel):
    rating: float
    review: Optional[str] = None

class WorkerRatingCreate(WorkerRatingBase):
    booking_id: Optional[int] = None


class WorkerReviewStatsResponse(BaseModel):
    totalReviews: int
    averageRating: float
    responseRate: int
    ratingBreakdown: Dict[int, int]


class WorkerRatingResponse(WorkerRatingBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


# ==========================
#  Worker Languages
# ==========================
class WorkerLanguageBase(BaseModel):
    language_id: int

class WorkerLanguageCreate(WorkerLanguageBase):
    pass

class WorkerLanguageResponse(WorkerLanguageBase):
    id: int
    language: LanguageResponse

    class Config:
        orm_mode = True


# ==========================
#  Worker Payments
# ==========================
class WorkerPaymentBase(BaseModel):
    amount: float
    payment_method: str
    paid_by: Optional[str] = None
    payment_reference: Optional[str] = None
    reference_number: Optional[str] = None

class WorkerPaymentCreate(WorkerPaymentBase):
    work_done: int   # booking_id

class WorkerPaymentResponse(WorkerPaymentBase):
    id: int
    payment_date: datetime

    class Config:
        orm_mode = True


# ==========================
#  Worker
# ==========================
class WorkerBase(BaseModel):
    worker_type: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    organization_name: Optional[str] = None
    phone_number: str
    address: Optional[str] = None
    profile_picture: Optional[str] = None
    national_id_number: str
    national_id_proof: Optional[str] = None
    good_conduct_number: Optional[str] = None
    good_conduct_proof: Optional[str] = None
    good_conduct_issue_date: Optional[datetime] = None
    good_conduct_expiry_date: Optional[datetime] = None
    mpesa_number: str
    bank_name: Optional[str] = None
    bank_account_name: Optional[str] = None
    bank_account_number: Optional[str] = None

class WorkerCreate(WorkerBase):
    user_id: int
    agreement_accepted: bool
    chat_policy_accepted: bool
    organization_id: Optional[int] = None
class WorkerUpdate(WorkerBase):
    pass


# --- Notification Schema ---

class NotificationBase(BaseModel):
    message: str
    type: str


class NotificationCreate(NotificationBase):
    user_id: int


class NotificationResponse(NotificationBase):
    id: int
    is_read: bool
    title: str
    created_at: datetime

    class Config:
        orm_mode = True

class Jobstats(BaseModel):
    total_jobs: Optional[int] = 1
    completed_jobs: Optional[int] = 1
    pending_jobs: Optional[int] = 1
    cancelled_jobs: Optional[int] = 1
    rejected_jobs: Optional[int] = 1
    accepted_jobs: Optional[int] = 1

class WorkerResponse(WorkerBase):
    id: int
    public_id: str
    average_rating: float
    jobs_completed: int
    notifications_enabled: bool
    chat_enabled: bool
    agreement_accepted: bool

    emergency_contacts: List[WorkerEmergencyContactResponse] = []
    equipments: List[WorkerEquipmentResponse] = []
    services: List[WorkerServiceResponse] = []
    availabilities: List[WorkerAvailabilityResponse] = []
    ratings: List[WorkerRatingResponse] = []
    languages: List[WorkerLanguageResponse] = []
    notifications: List[NotificationResponse] = []
    job_stats: Jobstats |None = None
    # we don’t embed payments by default (usually admin view only)

    class Config:
        orm_mode = True
        from_attributes = True
# ------------------------------``



class BookingServiceBase(BaseModel):
    feature_option_id: int
    quantity: int
    unit_price: float
    total_price: float


class BookingServiceCreate(BookingServiceBase):
    pass





# ------------------------------
# Booking Schemas
# ------------------------------

class ServiceFeatureBase(BaseModel):
    slug: str
    title: str
    description: Optional[str] = None
    icon_name: Optional[str] = None


class ServiceCategoryBOut(BaseModel):
   slug: str
   title: str
   class Config:
       from_attributes = True




class BookingServiceFeatureOut(BaseModel):
    slug: str
    title: str
    category: ServiceCategoryBOut

    class Config:
        from_attributes = True

class FeatureOptionBase(BaseModel):
    area_type: str
    label: str
    unit_price: float
    min_units: Optional[int] = 0
    max_units: Optional[int] = None


class FeatureOptionCreate(FeatureOptionBase):
    pass


class FeatureOptionOut(FeatureOptionBase):
    id: int
    feature: BookingServiceFeatureOut
    # category: ServiceCategoryBOut

    class Config:
        from_attributes = True
class BookingServiceResponse(BookingServiceBase):
    id: int
    feature_option: FeatureOptionOut

    class Config:
        from_attributes = True

class BookingBase(BaseModel):
    client_id: int
    worker_id: int
    appointment_datetime: datetime
    service_feature_id: int
    total_price: float
    deposit_paid: float 
    description:Optional[str] 
    location: str
    status: str 
    rating: Optional[float] 

class BookingCreate(BookingBase):
    booked_services: Optional[List[BookingServiceCreate]]=[]


class BookingUpdate(BaseModel):
    worker_id: Optional[int] = None
    appointment_datetime: Optional[datetime] = None
    total_price: Optional[float] = None
    deposit_paid: Optional[float] = None
    status: Optional[str] = None
    rating: Optional[float] =  None
    location: Optional[str] = None
    description: Optional[str] = None

class ClientName(BaseModel):
    id: int
    first_name: Optional[str]
    last_name: Optional[str]
    organization_name: Optional[str]

    class Config:
        from_attributes = True

class WorkerName(BaseModel):
    id: int
    first_name: str
    last_name: str

    class Config:
        from_attributes = True
        
    

class BookingResponse(BookingBase):
    id: int
    public_id: str
    date_of_booking: datetime
    booked_services: List[BookingServiceResponse]
    client: ClientName
    worker: WorkerName 
    # feature: ServiceFeatureBOut

    class Config:
        from_attributes = True


# ----- Feature Options -----


# ----- Service Feature -----

class ServiceFeatureCreate(ServiceFeatureBase):
    category_id: int
    options: Optional[List[FeatureOptionCreate]] = []


class ServiceFeatureOut(ServiceFeatureBase):
    id: int
    options: List[FeatureOptionOut]

    class Config:
        from_attributes = True



# ----- Service Category -----
class ServiceCategoryBase(BaseModel):
    slug: str
    title: str
    description: Optional[str] = None
    icon_name: Optional[str] = None


class ServiceCategoryCreate(ServiceCategoryBase):
    pass


class ServiceCategoryOut(ServiceCategoryBase):
    id: int
    features: List[ServiceFeatureOut]

    class Config:
        from_attributes = True


class BookingRequestBase(BaseModel):
    client_id: int
    service_feature_id: int
    appointment_datetime: datetime
    location: str
    description: Optional[str] = None
    pricing: Optional[float] = None
    status: Optional[str] = "pending"
    worker_id: int


class BookingRequestCreate(BookingRequestBase):
    pass


class BookingRequestUpdate(BaseModel):
    worker_id: Optional[int] = None
    appointment_datetime: Optional[datetime] = None
    location: Optional[str] = None
    description: Optional[str] = None
    pricing: Optional[float] = None
    status: Optional[str] = None

class ServiceFeatureOutBR(BaseModel):
    id: int
    title: str
    slug: str
    category: ServiceCategoryBOut

    class Config:
        from_attributes = True

class BookingRequestResponse(BookingRequestBase):
    id: int
    public_id: str
    worker_id: Optional[int] = None
    requested_date: datetime
    client: ClientName
    worker: WorkerName
    feature: ServiceFeatureOutBR
    

    class Config:
        orm_mode = True


class PaymentCreateResponse(BaseModel):
    client_secret: str
    payment_intent_id: str
    amount: float
    currency: str

class PaymentWebhookResponse(BaseModel):
    status: str
    payment_intent_id: str

    class Config:
        orm_mode = True

