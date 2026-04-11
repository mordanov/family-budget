from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.report import ReportFilter, ReportResponse, ForecastResponse, DailyBalanceResponse, ForecastDetailedResponse
from app.services.report_service import ReportService


def _prev_month_range():
    from datetime import date
    import calendar
    today = date.today()
    first_this = today.replace(day=1)
    last_prev = first_this.replace(day=1) - __import__('datetime').timedelta(days=1)
    first_prev = last_prev.replace(day=1)
    return (
        datetime(first_prev.year, first_prev.month, 1, tzinfo=timezone.utc),
        datetime(last_prev.year, last_prev.month, last_prev.day, 23, 59, 59, tzinfo=timezone.utc),
    )


router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/", response_model=ReportResponse)
async def get_report(
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    user_id: int | None = Query(None),
    category_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if not date_from or not date_to:
        date_from, date_to = _prev_month_range()
    filters = ReportFilter(
        date_from=date_from, date_to=date_to,
        user_id=user_id, category_id=category_id,
    )
    return await ReportService(db).get_report(filters)


@router.get("/forecast", response_model=ForecastResponse)
async def get_forecast(
    year: int | None = Query(None),
    month: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if not year or not month:
        from datetime import date
        today = date.today()
        if today.month == 12:
            year, month = today.year + 1, 1
        else:
            year, month = today.year, today.month + 1
    return await ReportService(db).get_forecast(year, month)


@router.get("/forecast-detailed", response_model=ForecastDetailedResponse)
async def get_forecast_detailed(
    days_elapsed: int = Query(1, ge=1, le=31),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await ReportService(db).get_forecast_detailed(days_elapsed)


@router.get("/balance-daily", response_model=DailyBalanceResponse)
async def get_balance_daily(
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if not date_from or not date_to:
        date_from, date_to = _prev_month_range()
    return await ReportService(db).get_daily_balance(date_from, date_to)

