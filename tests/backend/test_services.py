"""Additional service-level tests for edge cases and validators."""
import pytest
from decimal import Decimal

from app.utils.validators import (
    validate_amount,
    validate_email,
    validate_name,
    validate_year_month,
    validate_file_size,
    validate_mime_type,
    sanitize_description,
    ValidationError,
)
from app.utils.formatters import (
    format_currency,
    format_amount,
    format_file_size,
    truncate_text,
    format_percentage,
)


class TestValidators:
    def test_validate_amount_valid(self):
        assert validate_amount("100.50") == Decimal("100.50")
        assert validate_amount(99.99) == Decimal("99.99")
        assert validate_amount(Decimal("0.01")) == Decimal("0.01")

    def test_validate_amount_zero_raises(self):
        with pytest.raises(ValidationError):
            validate_amount(0)

    def test_validate_amount_negative_raises(self):
        with pytest.raises(ValidationError):
            validate_amount(-10)

    def test_validate_amount_exceeds_max(self):
        with pytest.raises(ValidationError):
            validate_amount(1_000_000_000)

    def test_validate_amount_non_numeric(self):
        with pytest.raises(ValidationError):
            validate_amount("not-a-number")

    def test_validate_amount_precision(self):
        result = validate_amount("9.999")
        assert result == Decimal("10.00")

    def test_validate_email_valid(self):
        assert validate_email("User@EXAMPLE.COM") == "user@example.com"
        assert validate_email("  test@test.org  ") == "test@test.org"

    def test_validate_email_invalid(self):
        for bad in ["not-an-email", "@nodomain", "nodot@com", ""]:
            with pytest.raises(ValidationError):
                validate_email(bad)

    def test_validate_name_valid(self):
        assert validate_name("  Hello  ") == "Hello"

    def test_validate_name_too_short(self):
        with pytest.raises(ValidationError):
            validate_name("", min_len=1)

    def test_validate_name_too_long(self):
        with pytest.raises(ValidationError):
            validate_name("x" * 300, max_len=255)

    def test_validate_year_month_valid(self):
        validate_year_month(2024, 6)  # should not raise

    def test_validate_year_month_invalid_month(self):
        with pytest.raises(ValidationError):
            validate_year_month(2024, 13)

    def test_validate_year_month_invalid_year(self):
        with pytest.raises(ValidationError):
            validate_year_month(1999, 1)

    def test_validate_file_size_ok(self):
        validate_file_size(100, 1024)  # no raise

    def test_validate_file_size_too_large(self):
        with pytest.raises(ValidationError):
            validate_file_size(1025, 1024)

    def test_validate_mime_type_ok(self):
        validate_mime_type("image/png", ["image/png", "image/jpeg"])

    def test_validate_mime_type_not_allowed(self):
        with pytest.raises(ValidationError):
            validate_mime_type("application/exe", ["image/png"])

    def test_sanitize_description_strips(self):
        result = sanitize_description("  hello  ")
        assert result == "hello"

    def test_sanitize_description_none(self):
        assert sanitize_description(None) is None

    def test_sanitize_description_empty(self):
        assert sanitize_description("   ") is None

    def test_sanitize_description_truncates(self):
        result = sanitize_description("a" * 2000, max_len=100)
        assert len(result) == 100

    def test_sanitize_description_removes_null_bytes(self):
        result = sanitize_description("hello\x00world")
        assert "\x00" not in result


class TestFormatters:
    def test_format_currency_usd(self):
        assert format_currency(1234.56, "USD") == "$1,234.56"

    def test_format_currency_eur(self):
        assert format_currency(100.0, "EUR") == "€100.00"

    def test_format_amount(self):
        assert format_amount(1000.0) == "1,000.00"

    def test_format_file_size_bytes(self):
        assert "B" in format_file_size(500)

    def test_format_file_size_kb(self):
        assert "KB" in format_file_size(2048)

    def test_format_file_size_mb(self):
        assert "MB" in format_file_size(2 * 1024 * 1024)

    def test_truncate_text_short(self):
        assert truncate_text("hello", 10) == "hello"

    def test_truncate_text_long(self):
        result = truncate_text("a" * 100, 20)
        assert len(result) == 20
        assert result.endswith("...")

    def test_truncate_text_none(self):
        assert truncate_text(None) == ""

    def test_format_percentage(self):
        assert format_percentage(25.0, 100.0) == "25.0%"

    def test_format_percentage_zero_total(self):
        assert format_percentage(50.0, 0.0) == "0.0%"
