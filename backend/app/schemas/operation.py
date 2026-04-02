from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, condecimal
from app.models.operation import OperationType, PaymentType
from app.schemas.category import CategoryResponse
from app.schemas.payment_method import PaymentMethodResponse
from app.schemas.user import UserResponse


class OperationBase(BaseModel):
    amount: condecimal(gt=0, decimal_places=2)
    currency: str = Field(default="EUR", max_length=3)
    type: OperationType
    payment_type: PaymentType = PaymentType.card
    payment_method_id: int | None = None
    description: str | None = None
    is_recurring: bool = False
    recurring_end_date: datetime | None = None
    operation_date: datetime
    category_id: int
    user_id: int


class OperationCreate(OperationBase):
    pass


class OperationUpdate(BaseModel):
    amount: condecimal(gt=0, decimal_places=2) | None = None
    currency: str | None = Field(None, max_length=3)
    type: OperationType | None = None
    payment_type: PaymentType | None = None
    payment_method_id: int | None = None
    description: str | None = None
    is_recurring: bool | None = None
    recurring_end_date: datetime | None = None
    operation_date: datetime | None = None
    category_id: int | None = None
    user_id: int | None = None


class AttachmentSummary(BaseModel):
    id: int
    filename: str
    original_filename: str
    mime_type: str
    file_size: int
    created_at: datetime

    model_config = {"from_attributes": True}


class OperationResponse(OperationBase):
    id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    category: CategoryResponse
    user: UserResponse
    payment_method: PaymentMethodResponse
    attachments: list[AttachmentSummary] = []

    model_config = {"from_attributes": True}


class OperationListResponse(BaseModel):
    items: list[OperationResponse]
    total: int
    page: int
    size: int
    pages: int


class OperationFilter(BaseModel):
    date_from: datetime | None = None
    date_to: datetime | None = None
    type: OperationType | None = None
    payment_type: PaymentType | None = None
    payment_method_id: int | None = None
    category_id: int | None = None
    user_id: int | None = None
    is_recurring: bool | None = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=15, ge=1, le=100)
