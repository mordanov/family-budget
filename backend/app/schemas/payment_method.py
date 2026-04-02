from datetime import datetime
from pydantic import BaseModel, Field


class PaymentMethodResponse(BaseModel):
    id: int
    key: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaymentMethodCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class PaymentMethodUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

