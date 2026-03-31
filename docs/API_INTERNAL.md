# Internal API Reference

This documents the service layer API — the contract between the UI and business logic.

## UserService

### `get_all() → list[User]`
Returns all active (non-deleted) users.

### `get_by_id(user_id: int) → Optional[User]`
Returns user by ID. Returns `None` if not found.

### `create(name: str, email: str) → User`
Creates a new user.
- Validates name (2–100 chars)
- Validates and lowercases email
- Raises `ValidationError("email")` if duplicate

### `update(user_id, name=None, email=None) → User`
Updates a user. Only provided fields are changed.
- Raises `ValidationError("id")` if not found

### `delete(user_id: int) → bool`
Soft-deletes a user. Returns `True` if deleted.

---

## CategoryService

### `get_all() → list[Category]`

### `get_by_id(category_id: int) → Category`
Raises `ValidationError("id")` if not found.

### `create(name, description=None, color="#808080", icon="📁", created_by=None) → Category`
- Name must be 1–100 chars and unique (case-insensitive)
- Raises `ValidationError("name")` on duplicate

### `update(category_id, name=None, description=None, color=None, icon=None) → Category`

### `delete(category_id: int) → bool`
Cannot delete the "Other" default category.

---

## OperationService

### `get_by_id(op_id: int) → Operation`
Raises `ValidationError("id")` if not found.

### `get_many(f: OperationFilter, limit=100, offset=0) → tuple[list[Operation], int]`
Returns `(operations, total_count)`.

#### OperationFilter fields
- `date_from`, `date_to` — datetime range
- `operation_type` — OperationType enum
- `payment_type` — PaymentType enum
- `category_id`, `user_id` — integer IDs
- `currency` — Currency enum
- `is_recurring` — bool
- `search` — text search on description

### `create(amount, currency, operation_type, payment_type, category_id, user_id, operation_date, ...) → Operation`
- Validates amount > 0, ≤ 999,999,999.99
- Validates payment_type is valid for the operation_type:
  - Expense: cash, debit_card, credit_card
  - Income: cash, debit_card, refund_to_debit, refund_to_credit
- Sanitizes description (max 1000 chars)

### `update(op_id, **kwargs) → Operation`
Partial update — only non-None fields changed.

### `delete(op_id: int) → bool`
Soft delete.

### `get_monthly_summary(year, month) → dict`
Returns: `{year, month, total_income, total_expense, net}`

---

## BalanceService

### `get_or_create(year: int, month: int) → MonthlyBalance`
Returns existing balance or calculates from previous month.

### `set_manual(year, month, debit_balance, credit_balance) → MonthlyBalance`
Manually override a month's opening balance.
- Validates year (2000–2100) and month (1–12)
- Validates balances ≥ 0

### `get_history(months=12) → list[MonthlyBalance]`

### `recalculate_from(year, month, months_ahead=3) → None`
Recalculates forward from given month.

---

## ReportService

### `by_category(date_from=None, date_to=None, operation_type=None) → list[dict]`
Returns: `[{category_name, operation_type, total, count}]`

### `by_user(date_from, date_to, operation_type=None) → list[dict]`
Returns: `[{user_name, operation_type, total, count}]`

### `by_payment_type(date_from, date_to, operation_type=None) → list[dict]`
Returns: `[{payment_type, operation_type, total, count}]`

### `by_month(year=None) → list[dict]`
Returns: `[{year, month, operation_type, total}]`

### `income_vs_expense(date_from=None, date_to=None) → dict`
Returns: `{income, expense, net, savings_rate}`

### `forecast_next_month(base_year, base_month) → dict`
Returns:
```python
{
  "year": int,
  "month": int,
  "forecast_income": float,
  "forecast_expense": float,
  "forecast_net": float,
  "recurring_details": [{"id", "description", "amount", "operation_type", ...}],
  "avg_income_base": float,   # 3-month average non-recurring income
  "avg_expense_base": float,  # 3-month average non-recurring expense
}
```

---

## AttachmentService

### `get_by_operation(operation_id: int) → list[Attachment]`

### `get_by_id(att_id: int) → Attachment`

### `upload(operation_id, file_name, file_bytes, mime_type) → Attachment`
- Validates file size ≤ MAX_FILE_SIZE_MB
- Validates MIME type is in allowed list
- Stores file in `{UPLOAD_DIR}/{operation_id}/{uuid}.ext`
- Creates DB record

### `delete(att_id: int) → bool`
Soft-deletes DB record and removes physical file.

### `read_file(att: Attachment) → Optional[bytes]`
Reads and returns file bytes, or `None` if file missing.

---

## Error Handling

All validation errors raise `app.utils.validators.ValidationError`:

```python
class ValidationError(Exception):
    field: str   # which field failed
    message: str # human-readable message
```

UI pages catch this and display `st.error(f"{e.field}: {e.message}")`.

Unexpected errors (DB failures, file I/O) are logged and re-raised as generic `Exception`.
