import pytest
from datetime import datetime, timezone
from decimal import Decimal

from app.services.report_service import ReportService
from app.services.operation_service import OperationService
from app.schemas.operation import OperationCreate
from app.schemas.report import ReportFilter


@pytest.mark.asyncio
async def test_report_empty_period(db, test_user, test_category):
    service = ReportService(db)
    filters = ReportFilter(
        date_from=datetime(2020, 1, 1, tzinfo=timezone.utc),
        date_to=datetime(2020, 1, 31, tzinfo=timezone.utc),
    )
    report = await service.get_report(filters)
    assert report.total_income == Decimal("0")
    assert report.total_expense == Decimal("0")
    assert report.net_balance == Decimal("0")


@pytest.mark.asyncio
async def test_report_with_operations(db, test_user, test_category):
    op_service = OperationService(db)
    await op_service.create(OperationCreate(
        amount=Decimal("500.00"),
        currency="EUR",
        type="income",
        payment_type="bank_transfer",
        operation_date=datetime(2023, 6, 15, tzinfo=timezone.utc),
        category_id=test_category.id,
        user_id=test_user.id,
    ))
    await op_service.create(OperationCreate(
        amount=Decimal("200.00"),
        currency="EUR",
        type="expense",
        payment_type="card",
        operation_date=datetime(2023, 6, 20, tzinfo=timezone.utc),
        category_id=test_category.id,
        user_id=test_user.id,
    ))

    report_service = ReportService(db)
    filters = ReportFilter(
        date_from=datetime(2023, 6, 1, tzinfo=timezone.utc),
        date_to=datetime(2023, 6, 30, tzinfo=timezone.utc),
    )
    report = await report_service.get_report(filters)
    assert report.total_income == Decimal("500.00")
    assert report.total_expense == Decimal("200.00")
    assert report.net_balance == Decimal("300.00")
    assert len(report.by_category) >= 1
    assert len(report.by_user) >= 1


@pytest.mark.asyncio
async def test_forecast_next_month(db, test_user, test_category):
    op_service = OperationService(db)
    # Add a recurring expense
    await op_service.create(OperationCreate(
        amount=Decimal("1200.00"),
        currency="EUR",
        type="expense",
        payment_type="bank_transfer",
        description="Rent",
        is_recurring=True,
        operation_date=datetime(2023, 5, 1, tzinfo=timezone.utc),
        category_id=test_category.id,
        user_id=test_user.id,
    ))

    report_service = ReportService(db)
    forecast = await report_service.get_forecast(2023, 7)
    assert forecast.year == 2023
    assert forecast.month == 7
    assert forecast.total_estimated_expense >= Decimal("1200.00")
    recurring_items = [i for i in forecast.items if i.source == "recurring"]
    assert len(recurring_items) >= 1


@pytest.mark.asyncio
async def test_monthly_trend_in_report(db, test_user, test_category):
    op_service = OperationService(db)
    for month in [1, 2, 3]:
        await op_service.create(OperationCreate(
            amount=Decimal("100.00"),
            currency="EUR",
            type="expense",
            payment_type="cash",
            operation_date=datetime(2024, month, 10, tzinfo=timezone.utc),
            category_id=test_category.id,
            user_id=test_user.id,
        ))

    report_service = ReportService(db)
    filters = ReportFilter(
        date_from=datetime(2024, 1, 1, tzinfo=timezone.utc),
        date_to=datetime(2024, 3, 31, tzinfo=timezone.utc),
    )
    report = await report_service.get_report(filters)
    assert len(report.monthly_trend) == 3
    for trend in report.monthly_trend:
        assert trend.total_expense == Decimal("100.00")
