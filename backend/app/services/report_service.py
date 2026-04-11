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
    ForecastDetailedResponse, CategoryForecastItem, MonthlyHistoryItem,
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
            c["category_icon"] = row.category_icon
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

    @staticmethod
    def _linear_regression(x: list[float], y: list[float]) -> tuple[float, float]:
        """Simple linear regression: returns (slope, intercept)."""
        n = len(x)
        if n < 2:
            return 0.0, float(y[0]) if n == 1 else 0.0
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi * xi for xi in x)
        denom = n * sum_x2 - sum_x * sum_x
        if denom == 0:
            return 0.0, sum_y / n
        slope = (n * sum_xy - sum_x * sum_y) / denom
        intercept = (sum_y - slope * sum_x) / n
        return slope, intercept

    async def get_forecast_detailed(
        self, days_elapsed: int
    ) -> ForecastDetailedResponse:
        now = datetime.now(timezone.utc)
        year, month = now.year, now.month
        days_in_month = calendar.monthrange(year, month)[1]
        days_elapsed = max(1, min(days_elapsed, days_in_month))

        # Current month range
        cur_from = datetime(year, month, 1, tzinfo=timezone.utc)
        cur_to = datetime(year, month, days_in_month, 23, 59, 59, tzinfo=timezone.utc)

        # 3-month history range (3 full months before current)
        hist_to = cur_from - timedelta(days=1)
        hist_from = hist_to.replace(day=1)
        for _ in range(2):
            hist_from = (hist_from - timedelta(days=1)).replace(day=1)

        # Fetch data
        hist_rows = await self.op_repo.get_category_monthly_totals(hist_from, hist_to)
        cur_rows = await self.op_repo.get_by_category_period(cur_from, cur_to)
        cur_totals = await self.op_repo.get_totals_by_period(cur_from, cur_to)

        # Build history per category: {cat_id -> {(year,month) -> expense}}
        cat_meta: dict[int, dict] = {}
        cat_history: dict[int, dict[tuple, Decimal]] = defaultdict(dict)

        for row in hist_rows:
            cid = row.category_id
            if cid not in cat_meta:
                cat_meta[cid] = {
                    "name": row.category_name,
                    "color": row.category_color,
                    "icon": row.category_icon,
                }
            key = (int(row.year), int(row.month))
            if row.type.value == "expense":
                cat_history[cid][key] = cat_history[cid].get(key, Decimal("0")) + (row.total or Decimal("0"))

        # Build current month actuals per category
        cur_cat_expense: dict[int, Decimal] = defaultdict(lambda: Decimal("0"))
        cur_cat_income: dict[int, Decimal] = defaultdict(lambda: Decimal("0"))
        for row in cur_rows:
            cid = row.category_id
            if cid not in cat_meta:
                cat_meta[cid] = {
                    "name": row.category_name,
                    "color": row.category_color,
                    "icon": row.category_icon,
                }
            if row.type.value == "expense":
                cur_cat_expense[cid] += row.total or Decimal("0")
            else:
                cur_cat_income[cid] += row.total or Decimal("0")

        # All category ids from history + current month
        all_cat_ids = set(cat_history.keys()) | set(cur_cat_expense.keys())

        # Build CategoryForecastItem per category
        categories: list[CategoryForecastItem] = []
        next_month_expense_total = Decimal("0")
        next_month_income_total = Decimal("0")

        for cid in all_cat_ids:
            meta = cat_meta.get(cid, {"name": "Unknown", "color": None, "icon": None})
            hist = cat_history.get(cid, {})

            # Sort history by (year, month)
            sorted_hist = sorted(hist.items())
            history_items = [
                MonthlyHistoryItem(year=k[0], month=k[1], expense=v)
                for k, v in sorted_hist
            ]

            actual = cur_cat_expense.get(cid, Decimal("0"))

            # Current month projection: extrapolate to full month
            avg_daily = float(actual) / days_elapsed
            cur_projected = Decimal(str(round(avg_daily * days_in_month, 2)))

            # Linear regression for next month
            x_vals = [float(i) for i in range(len(sorted_hist))]
            y_vals = [float(v) for _, v in sorted_hist]

            if len(x_vals) >= 2:
                slope, intercept = self._linear_regression(x_vals, y_vals)
                next_x = float(len(sorted_hist))
                raw = intercept + slope * next_x
                next_projected = Decimal(str(round(max(0.0, raw), 2)))
                trend_slope = round(slope, 2)
            elif len(x_vals) == 1:
                next_projected = Decimal(str(round(y_vals[0], 2)))
                trend_slope = 0.0
            else:
                # Only current month data — project using daily average
                next_projected = cur_projected
                trend_slope = 0.0

            next_month_expense_total += next_projected

            categories.append(CategoryForecastItem(
                category_id=cid,
                category_name=meta["name"],
                category_icon=meta["icon"],
                category_color=meta["color"],
                history=history_items,
                current_month_actual=actual,
                current_month_projected=cur_projected,
                next_month_projected=next_projected,
                trend_slope=trend_slope,
            ))

        # Sort by current month actual desc
        categories.sort(key=lambda c: c.current_month_actual, reverse=True)

        # Current month totals
        cur_expense = cur_totals.get("expense", Decimal("0"))
        cur_income = cur_totals.get("income", Decimal("0"))
        avg_daily_total = float(cur_expense) / days_elapsed
        projected_total = Decimal(str(round(avg_daily_total * days_in_month, 2)))

        return ForecastDetailedResponse(
            categories=categories,
            current_month_expense_actual=cur_expense,
            current_month_expense_projected=projected_total,
            current_month_income_actual=cur_income,
            days_elapsed=days_elapsed,
            days_in_month=days_in_month,
            next_month_projected_expense=next_month_expense_total,
            next_month_projected_income=next_month_income_total,
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

