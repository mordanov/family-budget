from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.payment_method import PaymentMethodCreate, PaymentMethodResponse, PaymentMethodUpdate
from app.services.payment_method_service import PaymentMethodService


router = APIRouter(prefix="/payment-methods", tags=["payment-methods"])


@router.get("/", response_model=list[PaymentMethodResponse])
async def list_payment_methods(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await PaymentMethodService(db).get_all()


@router.get("/{payment_method_id}", response_model=PaymentMethodResponse)
async def get_payment_method(
    payment_method_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await PaymentMethodService(db).get_by_id(payment_method_id)


@router.post("/", response_model=PaymentMethodResponse, status_code=201)
async def create_payment_method(
    data: PaymentMethodCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await PaymentMethodService(db).create(data)


@router.patch("/{payment_method_id}", response_model=PaymentMethodResponse)
async def update_payment_method(
    payment_method_id: int,
    data: PaymentMethodUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await PaymentMethodService(db).update(payment_method_id, data)


@router.delete("/{payment_method_id}", status_code=204)
async def delete_payment_method(
    payment_method_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    await PaymentMethodService(db).delete(payment_method_id)


