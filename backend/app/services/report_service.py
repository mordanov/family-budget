from collections import defaultdict
from decimal import Decimal
from datetime import datetime, timezone, timedelta
import calendar

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.operation_repository import OperationRepository
from app.schemas.report import (
    ReportFilter, ReportResponse, ForecastResponse,
    CategorySummary, UserSummary, PaymentTypeSummary,
    MonthlyTrend, ForecastItem, DailyBalanceResponse, DailyBalanceItem,
)


class ReportService:
    def __init__(self, db: AsyncSession):
        self.op_repo = OperationRepository(db)

    async def get_report(self, filters: ReportFilter) -> ReportResponse:
        totals = await self.op_repo.get_totals_by_period(filters.date_from, filters.date_to)
        by_cat_rows = await self.op_repo.get_by_category_period(filters.date_from, filters.date_to)
        by_user_rows = await self.op_repo.get_by_user_period(filters.date_from, filters.date_to)
        by_pt_rows = await self.op_repo.get_by_payment_type_period(filters.date_from, filters.date_to)
        trend_rows = await self.op_repo.get_monthly_trend(filters.date_from, filters.date_to)

        # Build by_category
        cat_map: dict[int, dict] = defaultdict(lambda: {
            "total_income": Decimal("0"), "total_expense": Decimal("0"), "count": 0
        })
        for row in by_cat_rows:
            c = cat_map[row.category_id]
            c["category_name"] = row.category_name
            c["category_color"] = row.category_color
            if row.type.value == "income":
                c["total_income"] += row.total or Decimal("0")
            else:
                c["total_expense"] += row.total or Decimal("0")
            c["count"] += row.count

        by_category = [
            CategorySummary(category_id=cid, **data)
            for cid, data in cat_map.items()
        ]

        # Build by_user
        user_map: dict[int, dict] = defaultdict(lambda: {
            "total_income": Decimal("0"), "total_expense": Decimal("0"), "count": 0
        })
        for row in by_user_rows:
            u = user_map[row.user_id]
            u["user_name"] = row.user_name
            if row.type.value == "income":
                u["total_income"] += row.total or Decimal("0")
            else:
                u["total_expense"] += row.total or Decimal("0")
            u["count"] += row.count

        by_user = [UserSummary(user_id=uid, **data) for uid, data in user_map.items()]

        # Build by_payment_type
        pt_map: dict[str, dict] = defaultdict(lambda: {
            "total_income": Decimal("0"), "total_expense": Decimal("0"), "count": 0
        })
        for row in by_pt_rows:
            pt = pt_map[row.payment_method_key]
            pt["payment_method_name"] = row.payment_method_name
            if row.type.value == "income":
                pt["total_income"] += row.total or Decimal("0")
            else:
                pt["total_expense"] += row.total or Decimal("0")
            pt["count"] += row.count

        by_payment_type = [
            PaymentTypeSummary(payment_type=pt, **data) for pt, data in pt_map.items()
        ]

        # Monthly trend
        trend_map: dict[tuple, dict] = defaultdict(lambda: {
            "total_income": Decimal("0"), "total_expense": Decimal("0")
        })
        for row in trend_rows:
            key = (int(row.year), int(row.month))
            if row.type.value == "income":
                trend_map[key]["total_income"] += row.total or Decimal("0")
            else:
                trend_map[key]["total_expense"] += row.total or Decimal("0")

        monthly_trend = [
            MonthlyTrend(
                year=y, month=m,
                total_income=d["total_income"],
                total_expense=d["total_expense"],
                net=d["total_income"] - d["total_expense"],
            )
            for (y, m), d in sorted(trend_map.items())
        ]

        income = totals.get("income", Decimal("0"))
        expense = totals.get("expense", Decimal("0"))

        return ReportResponse(
            date_from=filters.date_from,
            date_to=filters.date_to,
            total_income=income,
            total_expense=expense,
            net_balance=income - expense,
            by_category=by_category,
            by_user=by_user,
            by_payment_type=by_payment_type,
            monthly_trend=monthly_trend,
        )

    async def get_forecast(self, year: int, month: int) -> ForecastResponse:
        # Use last 3 months for average
        date_to = datetime(year, month, 1, tzinfo=timezone.utc) - timedelta(days=1)
        date_from = datetime(date_to.year, date_to.month, 1, tzinfo=timezone.utc)
        # Go back 3 months
        for _ in range(2):
            date_from = (date_from - timedelta(days=1)).replace(day=1)

        # Recurring operations
        as_of = datetime(year, month, 1, tzinfo=timezone.utc)
        recurring = await self.op_repo.get_recurring_active(as_of)

        items: list[ForecastItem] = []
        total_income = Decimal("0")
        total_expense = Decimal("0")

        # Add recurring
        seen_categories: set[int] = set()
        for op in recurring:
            items.append(ForecastItem(
                category_id=op.category_id,
                category_name=op.category.name,
                estimated_amount=op.amount,
                type=op.type.value,
                source="recurring",
            ))
            if op.type.value == "income":
                total_income += op.amount
            else:
                total_expense += op.amount
            seen_categories.add(op.category_id)

        # Average for non-recurring categories
        by_cat_rows = await self.op_repo.get_by_category_period(date_from, date_to)
        cat_totals: dict[int, dict] = defaultdict(lambda: {
            "income": Decimal("0"), "expense": Decimal("0"),
            "name": "", "months": set()
        })
        trend_rows = await self.op_repo.get_monthly_trend(date_from, date_to)
        months_with_data = {(int(r.year), int(r.month)) for r in trend_rows}
        num_months = max(len(months_with_data), 1)

        for row in by_cat_rows:
            if row.category_id not in seen_categories:
                cat_totals[row.category_id]["name"] = row.category_name
                if row.type.value == "income":
                    cat_totals[row.category_id]["income"] += row.total or Decimal("0")
                else:
                    cat_totals[row.category_id]["expense"] += row.total or Decimal("0")

        for cat_id, data in cat_totals.items():
            if data["income"] > 0:
                avg = data["income"] / num_months
                items.append(ForecastItem(
                    category_id=cat_id,
                    category_name=data["name"],
                    estimated_amount=avg,
                    type="income",
                    source="average",
                ))
                total_income += avg
            if data["expense"] > 0:
                avg = data["expense"] / num_months
                items.append(ForecastItem(
                    category_id=cat_id,
                    category_name=data["name"],
                    estimated_amount=avg,
                    type="expense",
                    source="average",
                ))
                total_expense += avg

        return ForecastResponse(
            year=year,
            month=month,
            items=items,
            total_estimated_income=total_income,
            total_estimated_expense=total_expense,
            estimated_net=total_income - total_expense,
        )

    async def get_daily_balance(self, date_from: datetime, date_to: datetime) -> DailyBalanceResponse:
        initial = await self.op_repo.get_balance_before(date_from)
        rows = await self.op_repo.get_daily_net(date_from, date_to)

        day_delta: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        for row in rows:
            key = str(row.day)
            sign = Decimal("1") if row.type.value == "income" else Decimal("-1")
            day_delta[key] += sign * (row.total or Decimal("0"))

        items: list[DailyBalanceItem] = []
        running = initial
        cursor = date_from.date()
        end = date_to.date()
        while cursor <= end:
            key = cursor.isoformat()
            running += day_delta.get(key, Decimal("0"))
            items.append(DailyBalanceItem(date=key, balance=running))
            cursor += timedelta(days=1)

        return DailyBalanceResponse(items=items)

