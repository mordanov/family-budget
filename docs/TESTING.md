# Testing Guide

## Overview

The test suite targets **≥85% code coverage** across all backend modules.

## Test Structure

```
tests/
├── backend/
│   ├── conftest.py          # DB fixtures, session loop, table cleanup
│   ├── test_users.py        # UserRepository + UserService (18 tests)
│   ├── test_categories.py   # CategoryRepository + CategoryService (14 tests)
│   ├── test_operations.py   # OperationRepository + OperationService (20 tests)
│   ├── test_balances.py     # BalanceRepository + BalanceService (12 tests)
│   ├── test_reports.py      # ReportService (9 tests)
│   └── test_services.py     # Validators + Formatters (35 unit tests)
└── frontend/
    ├── conftest.py          # Mock fixtures for UI data
    └── test_forms.py        # Charts, formatters, enum unit tests (22 tests)
```

## Running Tests

### All tests with coverage

```bash
pytest
```

### Unit tests only (no database required)

```bash
pytest tests/backend/test_services.py tests/frontend/ -v
```

### Integration tests (requires PostgreSQL)

```bash
# Set test database URL
export TEST_DATABASE_URL=postgresql://user:pass@localhost:5432/family_budget_test

pytest tests/backend/ --ignore=tests/backend/test_services.py -v
```

### Single test file

```bash
pytest tests/backend/test_operations.py -v
```

### Specific test

```bash
pytest tests/backend/test_operations.py::TestOperationService::test_create_expense -v
```

### Run with specific marker

```bash
pytest -m "not slow" -v
```

## Test Database Setup

```bash
# Create test database
createdb family_budget_test

# The conftest.py applies migrations automatically via apply_migrations fixture
# Tables are truncated before each test via clean_tables fixture
```

## Coverage Report

After running `pytest`, coverage reports are generated in:
- **Terminal**: `--cov-report=term-missing`
- **HTML**: `htmlcov/index.html` (open in browser)
- **XML**: `coverage.xml` (for CI/CD upload)

## Test Design Patterns

### Database isolation

Each test function gets clean tables via the `clean_tables` autouse fixture:

```python
@pytest_asyncio.fixture(autouse=True)
async def clean_tables(db_pool):
    yield
    async with db_pool.acquire() as conn:
        await conn.execute("TRUNCATE TABLE ... RESTART IDENTITY CASCADE")
```

### Async tests

All async tests use `pytest.mark.asyncio` with session-scoped event loop:

```python
@pytest.mark.asyncio
class TestUserService:
    async def test_create_user(self):
        svc = UserService()
        user = await svc.create("Alice", "alice@test.com")
        assert user.name == "Alice"
```

### Unit tests (no database)

Validator and formatter tests are pure Python — no DB fixture needed:

```python
class TestValidators:
    def test_validate_amount_valid(self):
        assert validate_amount("100.50") == Decimal("100.50")
```

### Frontend chart tests

Charts are tested for structure and data shape without rendering in a browser:

```python
def test_income_expense_bar_with_data(self):
    fig = income_expense_bar([...])
    assert len(fig.data) == 2
    assert fig.data[0].name == "Income"
```

## Adding New Tests

1. Add test file to `tests/backend/` or `tests/frontend/`
2. For DB tests: use `sample_user`, `sample_category`, `sample_operation` fixtures
3. For unit tests: no fixtures needed — just import and test
4. Mark slow tests with `@pytest.mark.slow`

## CI Pipeline

Tests run automatically on every push and pull request via `.github/workflows/ci.yml`:

1. Lint with `ruff`
2. Unit tests (no DB dependency)
3. Integration tests with PostgreSQL service container
4. Coverage must be ≥85% or pipeline fails
5. Coverage report uploaded to Codecov
