import re
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
from typing import Optional


class ValidationError(Exception):
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


def validate_amount(value) -> Decimal:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise ValidationError("amount", "Must be a valid number")
    if amount <= 0:
        raise ValidationError("amount", "Must be greater than zero")
    if amount > Decimal("999999999.99"):
        raise ValidationError("amount", "Exceeds maximum allowed value")
    return amount.quantize(Decimal("0.01"))


def validate_email(email: str) -> str:
    email = email.strip().lower()
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        raise ValidationError("email", "Invalid email format")
    return email


def validate_name(name: str, field: str = "name", min_len: int = 1, max_len: int = 255) -> str:
    name = name.strip()
    if len(name) < min_len:
        raise ValidationError(field, f"Must be at least {min_len} character(s)")
    if len(name) > max_len:
        raise ValidationError(field, f"Must not exceed {max_len} characters")
    return name


def validate_date_range(
    date_from: Optional[datetime],
    date_to: Optional[datetime],
) -> tuple[Optional[datetime], Optional[datetime]]:
    if date_from and date_to and date_from > date_to:
        raise ValidationError("date_range", "Start date must be before end date")
    return date_from, date_to


def validate_file_size(size_bytes: int, max_bytes: int) -> None:
    if size_bytes > max_bytes:
        max_mb = max_bytes / (1024 * 1024)
        raise ValidationError("file", f"File size exceeds {max_mb:.0f} MB limit")


def validate_mime_type(mime_type: str, allowed: list[str]) -> None:
    if mime_type not in allowed:
        raise ValidationError(
            "file",
            f"File type '{mime_type}' not allowed. Allowed: {', '.join(allowed)}",
        )


def validate_year_month(year: int, month: int) -> None:
    if not (1 <= month <= 12):
        raise ValidationError("month", "Month must be between 1 and 12")
    if not (2000 <= year <= 2100):
        raise ValidationError("year", "Year must be between 2000 and 2100")


def sanitize_description(text: Optional[str], max_len: int = 1000) -> Optional[str]:
    if text is None:
        return None
    text = text.strip()
    if not text:
        return None
    # Remove null bytes
    text = text.replace("\x00", "")
    return text[:max_len]
