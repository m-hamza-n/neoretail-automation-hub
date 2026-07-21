from datetime import datetime

from pydantic import BaseModel, ConfigDict


# Customer Schemas
class CustomerBase(BaseModel):
    name: str
    email: str
    phone: str | None = None
    total_spend: float = 0.0
    is_active: bool = True
    last_purchase_date: datetime | None = None


class CustomerCreate(CustomerBase):
    pass


class CustomerRead(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


# Order Schemas
class OrderBase(BaseModel):
    customer_id: int
    product_name: str
    quantity: int
    total_price: float
    status: str = "pending"
    discount_code: str | None = None


class OrderCreate(OrderBase):
    pass


class OrderRead(OrderBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


# Product Schemas
class ProductBase(BaseModel):
    name: str
    category: str
    price: float
    stock: int = 0
    description: str | None = None


class ProductCreate(ProductBase):
    pass


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


# SupportTicket Schemas
class SupportTicketBase(BaseModel):
    customer_id: int | None = None
    subject: str
    body: str
    category: str | None = None
    priority: str | None = None
    status: str = "open"


class SupportTicketCreate(SupportTicketBase):
    pass


class SupportTicketRead(SupportTicketBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    resolved_at: datetime | None = None


# Lead Schemas
class LeadBase(BaseModel):
    name: str
    platform: str
    followers: int | None = None
    niche: str | None = None
    contact_email: str | None = None
    profile_url: str | None = None
    status: str = "new"
    notes: str | None = None


class LeadCreate(LeadBase):
    pass


class LeadRead(LeadBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


# EmailLog Schemas
class EmailLogBase(BaseModel):
    customer_id: int
    email_type: str
    subject: str
    body: str
    status: str = "sent"


class EmailLogCreate(EmailLogBase):
    pass


class EmailLogRead(EmailLogBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sent_at: datetime


# WorkflowEvent Schemas
class WorkflowEventBase(BaseModel):
    event_type: str
    payload: dict | None = None
    status: str = "success"


class WorkflowEventCreate(WorkflowEventBase):
    pass


class WorkflowEventRead(WorkflowEventBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    triggered_at: datetime
