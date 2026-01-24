from pydantic import BaseModel, EmailStr, validator,Field
from enum import Enum
from typing import Optional, List,Dict,Literal,Any
from pydantic import BaseModel, field_validator,EmailStr
from datetime import datetime
from uuid import uuid4
from fastapi import Form, UploadFile, File

## enums for user role ###

class UserRoleEnum(str, Enum):
    client = "client"
    worker = "worker"
    admin = "admin"
    hr = "hr"
    manager = "manager"
    support = "support"
    finance = "finance"

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: Optional[UserRoleEnum] = "client"
    # role: Optional[str] = "client"

class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    is_verified: bool
    is_admin: bool
    public_user_id: str
    created_at: datetime

    class Config:
        from_attributes = True



# Admin schemas
class AdminDashboardStats(BaseModel):
    total_users: int
    users_today: int
    users_by_role: Dict[str, int]
    total_clients: int
    verified_clients: int
    total_workers: int
    verified_workers: int
    pending_verification: int
    total_bookings: int
    bookings_today: int
    pending_bookings: int
    completed_bookings: int
    total_revenue: float
    revenue_today: float
    recent_users: List[Any]
    recent_bookings: List[Any]

    
class AdminRegister(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone_number: str
    department: Optional[str] = "Administration"

# schemas.py - Add these schemas
class AdminProfileCreate(BaseModel):
    first_name: str
    last_name: str
    phone_number: str
    date_of_birth: Optional[datetime] = None
    address: Optional[str] = None
    employee_id: Optional[str] = None
    department: str = "Administration"
    employment_date: Optional[datetime] = None
    salary: Optional[float] = None
    bank_name: Optional[str] = None
    bank_account_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_branch: Optional[str] = None
    mpesa_number: Optional[str] = None
  

class AdminProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    address: Optional[str] = None
    department: Optional[str] = None
    salary: Optional[float] = None
    bank_name: Optional[str] = None
    bank_account_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_branch: Optional[str] = None
    mpesa_number: Optional[str] = None
   

class AdminProfileResponse(BaseModel):
    id: int
    user_id: int
    first_name: str
    last_name: str
    phone_number: str
    profile_picture: Optional[str] = None
    department: str
    salary: Optional[float] = None
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    mpesa_number: Optional[str] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class AdminProfileComplete(AdminProfileResponse):
    date_of_birth: Optional[datetime] = None
    address: Optional[str] = None
    employment_type: str
    bank_account_name: Optional[str] = None
    bank_branch: Optional[str] = None
    
    permissions: Dict[str, Any]
    access_level: str
    user: Optional[Any] = None

class AdminPaymentCreate(BaseModel):
    admin_id: int
    amount: float
    payment_type: str
    payment_method: str
    payment_period_start: Optional[datetime] = None
    payment_period_end: Optional[datetime] = None
    notes: Optional[str] = None

class AdminPaymentResponse(BaseModel):
    id: int
    admin_id: int
    amount: float
    currency: str
    payment_type: str
    payment_method: str
    payment_reference: Optional[str] = None
    payment_date: Optional[datetime] = None
    payment_period_start: Optional[datetime] = None
    payment_period_end: Optional[datetime] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime
    admin_profile: Optional[Any] = None
    
    class Config:
        from_attributes = True

class AdminPaymentSummary(BaseModel):
    total_payments: int
    total_amount: float
    pending_amount: float
    completed_amount: float
    average_payment: float

class AdminEarningsResponse(BaseModel):
    admin_id: int
    admin_name: str
    total_earnings: float
    current_month_total: float
    last_month_total: float
    percentage_change: float
    breakdown: Dict[str, float]
    salary: Optional[float] = None
    payment_count: int

class UserManagementResponse(BaseModel):
    id: int
    email: str
    role: str
    last_seen: Optional[datetime]


class PaginatedUsersResponse(BaseModel):
    users: List[UserManagementResponse]
    total: int
    page: int
    limit: int
    pages: int

class BankDetailsResponse(BaseModel):
    bank_name: str
    account_name: str
    account_number: str
    branch: Optional[str] = None
    mpesa_number: Optional[str] = None
class UserManagementResponse(BaseModel):
    id: int
    email: str
    role: str
    is_verified: bool
    is_admin: bool
    public_user_id: str
    created_at: datetime
    last_seen: Optional[datetime]
    
    class Config:
        from_attributes = True

class AdminProfileCreate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    department: Optional[str] = None
    permissions: Optional[Dict[str, bool]] = None

class AdminProfileResponse(BaseModel):
    id: int
    user_id: int
    first_name: Optional[str]
    last_name: Optional[str]
    phone_number: Optional[str]
    department: Optional[str]
    permissions: Dict[str, bool]
    created_at: datetime
    
    class Config:
        from_attributes = True

# HR schemas
class WorkerVerificationRequest(BaseModel):
    approve: bool = True
    verify_good_conduct: bool = False
    verify_company_reg: bool = False
    rejection_reason: Optional[str] = None

class WorkerPerformanceResponse(BaseModel):
    worker_id: int
    name: str
    email: str
    phone: str
    average_rating: float
    jobs_completed: int
    completion_rate: float
    verification_status: bool
    recent_ratings: List[Any]

class HRDashboardStats(BaseModel):
    total_workers: int
    active_workers: int
    pending_verification: int
    recent_registrations: List[Any]
    top_performers: List[Any]
    low_performers: List[Any]

class PayrollSummary(BaseModel):
    worker_id: int
    worker_name: str
    total_amount: float
    payment_count: int
    payments: List[Any]

class BookingAnalytics(BaseModel):
    bookings_by_period: List[Dict[str, Any]]
    status_distribution: Dict[str, int]


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
    booking_id: int 


class WorkerReviewStatsResponse(BaseModel):
    totalReviews: int
    averageRating: float
    responseRate: int
    ratingBreakdown: Dict[int, int]

class CustomerRatersResponse(BaseModel):
    id: int
    first_name: Optional[str]
    last_name: Optional[str]
    organization_name: Optional[str]
    profile_picture: Optional[str]

    class Config:
        from_attributes = True


# class WorkerRatingResponse(WorkerRatingBase):
#     id: int
#     created_at: datetime
#     customer: CustomerRatersResponse


#     class Config:
#         orm_mode = True
    

#     @classmethod
#     def from_orm(cls, obj):
#         # This runs for every rating
#         rating = super().from_orm(obj)
#         if obj.booking and obj.booking.client:
#             rating.customer = CustomerRatersResponse.from_orm(obj.booking.client)
#         else:
#             rating.customer = None
#         return rating


class WorkerRatingResponse(WorkerRatingBase, from_attributes=True):
    id: int
    created_at: datetime
    booking_id: int
    # booking: Optional[BookingB]
    # customer: CustomerRatersResponse
    print("Inside WorkerRatingResponse schema", CustomerRatersResponse)

    @classmethod
    def from_orm(cls, obj):
        rating = super().from_orm(obj)
        if obj.booking and obj.booking.client:
            rating.customer = CustomerRatersResponse.from_orm(obj.booking.client)
        else:
            rating.customer = None
        return rating

        
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
class BookingClientOnly(BaseModel):
    id: int
    public_id: str
    client: ClientName

    class Config:
        from_attributes = True

class WorkerReviewRatingResponse(WorkerRatingResponse):
    booking: Optional[BookingClientOnly]

    class Config:
        from_attributes = True


class WorkerPaymentsBase(BaseModel):
    amount: float
    payment_method: str
    paid_by: Optional[str] = None
    payment_reference: Optional[str] = None
    reference_number: Optional[str] = None
    work_done: int   # booking_id

class WorkerPaymentsCreate(WorkerPaymentsBase):
    pass
class WorkerPaymentsResponse(WorkerPaymentsBase):
    id: int
    payment_date: datetime


    class Config:
        orm_mode = True


class EarningsChartItem(BaseModel):
    day: str
    earnings: float


class EarningsSummaryResponse(BaseModel):
    total: float
    thisWeek: float
    thisMonth: float
    pending: float
    lastWeekChange: float
    lastMonthChange: float


# schemas/message.py

class SendMessageRequest(BaseModel):
    booking_id: int
    sender_id: int
    receiver_id: int
    content: str



class MessageCreate(BaseModel):
    booking_id: int
    content: str
    sender_type: str      # add this for testing
    receiver_type: str    # add this for testing
    # Add this field for user_id
    user_id: Optional[int] = None  # For backward compatibility

class MarkReadRequest(BaseModel):
    message_id: int
    # Add this field for user_id
    user_id: Optional[int] = None  # For backward compatibility



class MessageResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    booking_id: int
    content: str
    sent_at: datetime
    is_read: bool

    class Config:
        from_attributes = True

class MessageItem(BaseModel):
    id: int
    sender: str  # "client" or "provider"
    text: str
    timestamp: str
    read: bool

class UserSummary(BaseModel):
    name: str
    profilePicture: str | None
    rating: float | None
    status: str  # "online" or "last seen X mins ago"

class ConversationResponse(BaseModel):
    bookingId: int
    client: UserSummary
    provider: UserSummary
    lastMessage: str | None
    timestamp: str | None
    unread: int
    messages: List[MessageItem]

    class Config:
        orm_mode = True