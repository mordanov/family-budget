from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.payment_method import PaymentMethodResponse, PaymentMethodUpdate
from app.services.payment_method_service import PaymentMethodService


router = APIRouter(prefix="/payment-methods", tags=["payment-methods"])


@router.get("/", response_model=list[PaymentMethodResponse])
async def list_payment_methods(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await PaymentMethodService(db).get_all()


@router.patch("/{payment_method_id}", response_model=PaymentMethodResponse)
async def update_payment_method(
    payment_method_id: int,
    data: PaymentMethodUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await PaymentMethodService(db).update(payment_method_id, data)

