from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, condecimal


class MonthlyBalanceResponse(BaseModel):
    id: int
    year: int
    month: int
    total_income: Decimal
    total_expense: Decimal
    opening_balance: Decimal
    closing_balance: Decimal
    is_manually_adjusted: bool
    manual_opening_balance: Decimal | None
    updated_at: datetime

    model_config = {"from_attributes": True}


class MonthlyBalanceUpdate(BaseModel):
    manual_opening_balance: condecimal(decimal_places=2)


# ─── Report Schemas ───────────────────────────────────────────────────────────

class ReportFilter(BaseModel):
    date_from: datetime
    date_to: datetime
    user_id: int | None = None
    category_id: int | None = None


class CategorySummary(BaseModel):
    category_id: int
    category_name: str
    category_color: str | None
    category_icon: str | None
    total_income: Decimal
    total_expense: Decimal
    count: int


class UserSummary(BaseModel):
    user_id: int
    user_name: str
    total_income: Decimal
    total_expense: Decimal
    count: int


class PaymentTypeSummary(BaseModel):
    payment_type: str
    payment_method_name: str | None = None
    total_income: Decimal
    total_expense: Decimal
    count: int


class MonthlyTrend(BaseModel):
    year: int
    month: int
    total_income: Decimal
    total_expense: Decimal
    net: Decimal


class ForecastItem(BaseModel):
    category_id: int
    category_name: str
    estimated_amount: Decimal
    type: str
    source: str  # "recurring" | "average"


class ReportResponse(BaseModel):
    date_from: datetime
    date_to: datetime
    total_income: Decimal
    total_expense: Decimal
    net_balance: Decimal
    by_category: list[CategorySummary]
    by_user: list[UserSummary]
    by_payment_type: list[PaymentTypeSummary]
    monthly_trend: list[MonthlyTrend]


class ForecastResponse(BaseModel):
    year: int
    month: int
    items: list[ForecastItem]
    total_estimated_income: Decimal
    total_estimated_expense: Decimal
    estimated_net: Decimal


class DailyBalanceItem(BaseModel):
    date: str
    balance: Decimal


class DailyBalanceResponse(BaseModel):
    items: list[DailyBalanceItem]


# ─── Forecast Detailed Schemas ────────────────────────────────────────────────

class MonthlyHistoryItem(BaseModel):
    year: int
    month: int
    expense: Decimal


class CategoryForecastItem(BaseModel):
    category_id: int
    category_name: str
    category_icon: str | None
    category_color: str | None
    history: list[MonthlyHistoryItem]        # last 3 months of expense
    current_month_actual: Decimal            # expense so far this month
    current_month_projected: Decimal         # projected to end of current month
    next_month_projected: Decimal            # linear regression projection
    trend_slope: float                       # €/month change (positive = growing)


class ForecastDetailedResponse(BaseModel):
    categories: list[CategoryForecastItem]
    # Current month
    current_month_expense_actual: Decimal
    current_month_expense_projected: Decimal
    current_month_income_actual: Decimal
    days_elapsed: int
    days_in_month: int
    # Next month totals
    next_month_projected_expense: Decimal
    next_month_projected_income: Decimal

