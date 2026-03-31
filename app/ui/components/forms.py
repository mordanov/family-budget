"""Reusable Streamlit form components."""
import streamlit as st
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from app.models.enums import (
    OperationType, PaymentType, Currency,
    EXPENSE_PAYMENT_TYPES, INCOME_PAYMENT_TYPES,
    PAYMENT_TYPE_LABELS, OPERATION_TYPE_LABELS,
)
from app.utils.formatters import format_currency


def operation_type_selector(key: str = "op_type") -> OperationType:
    options = list(OperationType)
    labels = [OPERATION_TYPE_LABELS[o] for o in options]
    idx = st.selectbox("Operation Type", labels, key=key)
    return options[labels.index(idx)]


def payment_type_selector(
    op_type: OperationType,
    key: str = "pay_type",
    default: Optional[PaymentType] = None,
) -> PaymentType:
    if op_type == OperationType.EXPENSE:
        options = EXPENSE_PAYMENT_TYPES
    else:
        options = INCOME_PAYMENT_TYPES

    labels = [PAYMENT_TYPE_LABELS[p] for p in options]
    default_idx = 0
    if default and default in options:
        default_idx = options.index(default)

    idx = st.selectbox("Payment Type", labels, index=default_idx, key=key)
    return options[labels.index(idx)]


def currency_selector(key: str = "currency", default: str = "USD") -> Currency:
    options = list(Currency)
    values = [c.value for c in options]
    default_idx = values.index(default) if default in values else 0
    selected = st.selectbox("Currency", values, index=default_idx, key=key)
    return Currency(selected)


def amount_input(key: str = "amount", default: float = 0.0) -> Optional[Decimal]:
    val = st.number_input(
        "Amount",
        min_value=0.01,
        max_value=999_999_999.99,
        value=max(default, 0.01),
        step=0.01,
        format="%.2f",
        key=key,
    )
    if val and val > 0:
        return Decimal(str(val))
    return None


def date_input(
    label: str = "Date",
    key: str = "date",
    default: Optional[date] = None,
) -> Optional[datetime]:
    d = st.date_input(label, value=default or date.today(), key=key)
    if d:
        return datetime.combine(d, datetime.min.time())
    return None


def category_selector(
    categories: list,
    key: str = "category",
    default_id: Optional[int] = None,
) -> Optional[int]:
    if not categories:
        st.warning("No categories available.")
        return None

    options = {c.id: f"{c.icon or ''} {c.name}" for c in categories}
    ids = list(options.keys())
    labels = list(options.values())

    default_idx = 0
    if default_id and default_id in ids:
        default_idx = ids.index(default_id)

    selected_label = st.selectbox("Category", labels, index=default_idx, key=key)
    return ids[labels.index(selected_label)]


def user_selector(
    users: list,
    key: str = "user",
    default_id: Optional[int] = None,
) -> Optional[int]:
    if not users:
        st.warning("No users available.")
        return None

    options = {u.id: u.name for u in users}
    ids = list(options.keys())
    labels = list(options.values())

    default_idx = 0
    if default_id and default_id in ids:
        default_idx = ids.index(default_id)

    selected_label = st.selectbox("User", labels, index=default_idx, key=key)
    return ids[labels.index(selected_label)]


def description_input(key: str = "description", default: str = "") -> Optional[str]:
    val = st.text_area("Description (optional)", value=default, max_chars=1000, key=key)
    return val.strip() if val and val.strip() else None


def recurring_inputs(
    key_prefix: str = "rec",
) -> tuple[bool, Optional[date]]:
    is_recurring = st.checkbox("Recurring expense", key=f"{key_prefix}_is_recurring")
    forecast_end_date = None
    if is_recurring:
        end_date = st.date_input(
            "Forecast end date (optional)",
            value=None,
            key=f"{key_prefix}_end_date",
        )
        forecast_end_date = end_date if end_date else None
    return is_recurring, forecast_end_date


def date_range_selector(
    key_prefix: str = "dr",
    default_year: Optional[int] = None,
    default_month: Optional[int] = None,
) -> tuple[datetime, datetime]:
    import calendar
    now = datetime.now()
    y = default_year or now.year
    m = default_month or now.month

    col1, col2 = st.columns(2)
    with col1:
        date_from = st.date_input("From", value=date(y, m, 1), key=f"{key_prefix}_from")
    with col2:
        last_day = calendar.monthrange(y, m)[1]
        date_to = st.date_input("To", value=date(y, m, last_day), key=f"{key_prefix}_to")

    return (
        datetime.combine(date_from, datetime.min.time()),
        datetime.combine(date_to, datetime(2000, 1, 1, 23, 59, 59).time()),
    )
