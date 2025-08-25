from pydantic import BaseModel, EmailStr, validator
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, field_validator
from typing import Optional, Literal
from datetime import datetime
from uuid import uuid4


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
class WorkerBase(BaseModel):
    first_name: str
    last_name: str
    phone_number: str
    address: Optional[str] = None
    user_id: int

class WorkerOut(WorkerBase):
    id: int
    public_id: str
    profile_picture: Optional[str] = None
    user_id: int
    good_conduct_proof: Optional[str] = None
    national_id_number: Optional[int] = None
    national_id_proof: Optional[str] = None
    


    class Config:
        from_attributes = True



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
    appointment_date: datetime
    location: str
    description: Optional[str] = None
    pricing: Optional[float] = None
    status: Optional[str] = "pending"
    worker_id: int


class BookingRequestCreate(BookingRequestBase):
    pass


class BookingRequestUpdate(BaseModel):
    worker_id: Optional[int] = None
    appointment_date: Optional[datetime] = None
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
