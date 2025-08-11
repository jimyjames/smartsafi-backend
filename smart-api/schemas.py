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
    client_id: int
    national_id_proof:Optional[str]
    tax_document_proof:Optional[str]
    profile_picture:Optional[str]

    class Config:
        from_attributes = True

class BookingBase(BaseModel):
    client_id: int
    worker_id: int
    scheduled_time: datetime  # Time in HH:MM format
    description: Optional[str] = None
    service_name: Optional[str] = None
    property_type: Optional[str] = None
    instructions: Optional[str] = None
    location_pin: Optional[str] = None
    total_price: float

  

class BookingPayment(BaseModel):
    public_id: str
    amount: float
    payment_method: str  # e.g., "credit_card", "paypal"


class BookingOut(BookingBase):
    id: int
    status: Optional[str] = "pending"  # e.g., "pending", "confirmed", "completed", "cancelled"
    created_at: datetime  # ISO format date string   
    updated_at: datetime  # ISO format date string
    public_id: str
    total_price: float
    deposit_paid: float
    payment_status: str  # e.g., "pending", "paid", "partial", "cancelled"  
    class Config:
        from_attributes = True

class WorkerBase(BaseModel):
    first_name: str
    last_name: str
    phone_number: str
    address: Optional[str] = None
    user_id: int

class WorkerOut(WorkerBase):
    worker_id: int
    public_id: str
    profile_picture: Optional[str] = None
    user_id: int
    good_conduct_proof: Optional[str] = None
    national_id_number: Optional[int] = None
    national_id_proof: Optional[str] = None
    


    class Config:
        from_attributes = True


# class ServiceNameBase(BaseModel):

#     name: str
# class ServiceDescriptionBase(BaseModel):
#     title: str
#     description: str
#     service_name_id: int

# class ServiceFeatureBase(BaseModel):
#     name: str
#     service_description_id: int
#     icon: Optional[str] = None


#     @property
#     def price(self):
#         return self.prices[0] if self.prices else None

# class ServicePriceBase(BaseModel):
#     amount: float
#     # unit: Optional[str] = "KES"  # or e.g., "per room", "per item"
#     service_description_id: int
#     service_feature_id: int

# # class ServicePriceOut(ServicePriceBase):
# #     amount: float
# #     unit: Optional[str]

# #     class Config:
# #         from_attributes = True


# # class ServiceFeatureOut(ServiceFeatureBase):
# #     id: int
# #     icon: Optional[str]
# #     prices: Optional[ServicePriceOut]  # Nested price object

# #     class Config:
# #         from_attributes = True
# class ServicePriceOut(BaseModel):
#     id: int
#     amount: float
#     unit: str

#     class Config:
#         from_attributes = True


# class ServiceDescriptionSimple(BaseModel):
#     id: int
#     title: str
#     service_name: "ServiceNameSimple"

#     class Config:
#         from_attributes = True


# class ServiceNameSimple(BaseModel):
#     id: int
#     name: str

#     class Config:
#         from_attributes = True


# ServiceDescriptionSimple.update_forward_refs()


# class ServiceFeatureOut(BaseModel):
#     id: int
#     name: str
#     icon: Optional[str]
#     prices: List[ServicePriceOut]
#     service_description: ServiceDescriptionSimple

#     class Config:
#         from_attributes = True


# class ServiceDescriptionOut(ServiceDescriptionBase):
#     id: int
#     features: List[ServiceFeatureOut] = []

#     class Config:
#         from_attributes = True

# class ServiceNameOut(ServiceNameBase):
#     id: int
#     descriptions: List[ServiceDescriptionOut] = []

#     class Config:
#         from_attributes = True


# class ServiceFeatureOut(ServiceFeatureBase):
#     id: int
#     service_description_id: int
#     icon: Optional[str] = None

#     class Config:
#         from_attributes = True


########################################3333



# ----- Feature Options -----
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

    class Config:
        orm_mode = True


# ----- Service Feature -----
class ServiceFeatureBase(BaseModel):
    slug: str
    title: str
    description: Optional[str] = None
    icon_name: Optional[str] = None


class ServiceFeatureCreate(ServiceFeatureBase):
    category_id: int
    options: Optional[List[FeatureOptionCreate]] = []


class ServiceFeatureOut(ServiceFeatureBase):
    id: int
    options: List[FeatureOptionOut]

    class Config:
        orm_mode = True


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
        orm_mode = True

