from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.report import MonthlyBalanceResponse, MonthlyBalanceUpdate
from app.services.balance_service import BalanceService

router = APIRouter(prefix="/balances", tags=["balances"])


@router.get("/", response_model=list[MonthlyBalanceResponse])
async def list_balances(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await BalanceService(db).get_all()


@router.get("/{year}/{month}", response_model=MonthlyBalanceResponse)
async def get_balance(
    year: int,
    month: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await BalanceService(db).get_month(year, month)


@router.patch("/{year}/{month}", response_model=MonthlyBalanceResponse)
async def set_opening_balance(
    year: int,
    month: int,
    data: MonthlyBalanceUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await BalanceService(db).set_manual_opening(year, month, data)
