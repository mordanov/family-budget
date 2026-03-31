from decimal import Decimal
from datetime import datetime, date
from typing import Optional


CURRENCY_SYMBOLS = {
    "USD": "$",
    "EUR": "€",
    "RUB": "₽",
    "GBP": "£",
}


def format_currency(amount: Decimal | float, currency: str = "USD") -> str:
    symbol = CURRENCY_SYMBOLS.get(currency, currency)
    return f"{symbol}{float(amount):,.2f}"


def format_amount(amount: Decimal | float) -> str:
    return f"{float(amount):,.2f}"


def format_date(dt: Optional[datetime | date], fmt: str = "%d %b %Y") -> str:
    if dt is None:
        return "—"
    return dt.strftime(fmt)


def format_datetime(dt: Optional[datetime], fmt: str = "%d %b %Y %H:%M") -> str:
    if dt is None:
        return "—"
    return dt.strftime(fmt)


def format_month_year(year: int, month: int) -> str:
    d = date(year, month, 1)
    return d.strftime("%B %Y")


def format_percentage(value: float, total: float) -> str:
    if total == 0:
        return "0.0%"
    pct = (value / total) * 100
    return f"{pct:.1f}%"


def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def truncate_text(text: Optional[str], max_len: int = 50) -> str:
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def month_name(month: int) -> str:
    from calendar import month_abbr
    return month_abbr[month]


def operation_type_badge(op_type: str) -> str:
    badges = {
        "expense": "🔴 Expense",
        "income": "🟢 Income",
    }
    return badges.get(op_type, op_type)


def payment_type_label(payment_type: str) -> str:
    labels = {
        "cash": "💵 Cash",
        "debit_card": "💳 Debit",
        "credit_card": "💳 Credit",
        "refund_to_debit": "↩️ Refund→Debit",
        "refund_to_credit": "↩️ Refund→Credit",
    }
    return labels.get(payment_type, payment_type)
