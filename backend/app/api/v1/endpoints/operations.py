from fastapi import APIRouter, Depends, Query
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.operation import OperationType, PaymentType
from app.schemas.operation import (
    OperationCreate, OperationUpdate, OperationResponse,
    OperationListResponse, OperationFilter,
)
from app.services.operation_service import OperationService

router = APIRouter(prefix="/operations", tags=["operations"])


@router.get("/", response_model=OperationListResponse)
async def list_operations(
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    type: OperationType | None = Query(None),
    payment_type: PaymentType | None = Query(None),
    category_id: int | None = Query(None),
    user_id: int | None = Query(None),
    is_recurring: bool | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    filters = OperationFilter(
        date_from=date_from, date_to=date_to, type=type,
        payment_type=payment_type, category_id=category_id,
        user_id=user_id, is_recurring=is_recurring,
        page=page, size=size,
    )
    return await OperationService(db).get_list(filters)


@router.get("/{operation_id}", response_model=OperationResponse)
async def get_operation(
    operation_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await OperationService(db).get_by_id(operation_id)


@router.post("/", response_model=OperationResponse, status_code=201)
async def create_operation(
    data: OperationCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await OperationService(db).create(data)


@router.patch("/{operation_id}", response_model=OperationResponse)
async def update_operation(
    operation_id: int,
    data: OperationUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await OperationService(db).update(operation_id, data)


@router.delete("/{operation_id}", status_code=204)
async def delete_operation(
    operation_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    await OperationService(db).delete(operation_id)
