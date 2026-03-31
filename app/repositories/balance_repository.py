from typing import Optional
from decimal import Decimal
import asyncpg

from app.repositories.base_repository import BaseRepository
from app.models.balance import MonthlyBalance, RecurringRule, CreateRecurringRuleDTO


class BalanceRepository(BaseRepository):
    def __init__(self):
        super().__init__("monthly_balances")

    async def get_by_id(
        self, balance_id: int, conn: Optional[asyncpg.Connection] = None
    ) -> Optional[MonthlyBalance]:
        query = """
            SELECT id, year, month, debit_balance, credit_balance,
                   is_manual, previous_month_id, created_at, updated_at
            FROM monthly_balances
            WHERE id = $1
        """
        record = await self.fetch_one(query, balance_id, conn=conn)
        return MonthlyBalance.from_record(dict(record)) if record else None

    async def get_by_month(
        self, year: int, month: int, conn: Optional[asyncpg.Connection] = None
    ) -> Optional[MonthlyBalance]:
        query = """
            SELECT id, year, month, debit_balance, credit_balance,
                   is_manual, previous_month_id, created_at, updated_at
            FROM monthly_balances
            WHERE year = $1 AND month = $2
        """
        record = await self.fetch_one(query, year, month, conn=conn)
        return MonthlyBalance.from_record(dict(record)) if record else None

    async def get_all(
        self, conn: Optional[asyncpg.Connection] = None
    ) -> list[MonthlyBalance]:
        query = """
            SELECT id, year, month, debit_balance, credit_balance,
                   is_manual, previous_month_id, created_at, updated_at
            FROM monthly_balances
            ORDER BY year DESC, month DESC
        """
        records = await self.fetch_many(query, conn=conn)
        return [MonthlyBalance.from_record(dict(r)) for r in records]

    async def upsert(
        self,
        year: int,
        month: int,
        debit_balance: Decimal,
        credit_balance: Decimal,
        is_manual: bool = False,
        previous_month_id: Optional[int] = None,
        conn: Optional[asyncpg.Connection] = None,
    ) -> MonthlyBalance:
        query = """
            INSERT INTO monthly_balances (year, month, debit_balance, credit_balance, is_manual, previous_month_id)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (year, month) DO UPDATE
            SET debit_balance = EXCLUDED.debit_balance,
                credit_balance = EXCLUDED.credit_balance,
                is_manual = EXCLUDED.is_manual,
                previous_month_id = COALESCE(EXCLUDED.previous_month_id, monthly_balances.previous_month_id),
                updated_at = NOW()
            RETURNING id, year, month, debit_balance, credit_balance,
                      is_manual, previous_month_id, created_at, updated_at
        """
        record = await self.fetch_one(
            query, year, month, debit_balance, credit_balance, is_manual, previous_month_id,
            conn=conn,
        )
        return MonthlyBalance.from_record(dict(record))

    async def get_history(
        self, months: int = 12, conn: Optional[asyncpg.Connection] = None
    ) -> list[MonthlyBalance]:
        query = """
            SELECT id, year, month, debit_balance, credit_balance,
                   is_manual, previous_month_id, created_at, updated_at
            FROM monthly_balances
            ORDER BY year DESC, month DESC
            LIMIT $1
        """
        records = await self.fetch_many(query, months, conn=conn)
        return [MonthlyBalance.from_record(dict(r)) for r in records]


class RecurringRuleRepository(BaseRepository):
    def __init__(self):
        super().__init__("recurring_rules")

    async def get_by_id(
        self, rule_id: int, conn: Optional[asyncpg.Connection] = None
    ) -> Optional[RecurringRule]:
        query = """
            SELECT id, name, amount, currency, operation_type, payment_type,
                   category_id, user_id, description, frequency, end_date,
                   created_at, updated_at, deleted_at
            FROM recurring_rules
            WHERE id = $1 AND deleted_at IS NULL
        """
        record = await self.fetch_one(query, rule_id, conn=conn)
        return RecurringRule.from_record(dict(record)) if record else None

    async def get_all_active(
        self, conn: Optional[asyncpg.Connection] = None
    ) -> list[RecurringRule]:
        query = """
            SELECT id, name, amount, currency, operation_type, payment_type,
                   category_id, user_id, description, frequency, end_date,
                   created_at, updated_at, deleted_at
            FROM recurring_rules
            WHERE deleted_at IS NULL
              AND (end_date IS NULL OR end_date >= CURRENT_DATE)
            ORDER BY name ASC
        """
        records = await self.fetch_many(query, conn=conn)
        return [RecurringRule.from_record(dict(r)) for r in records]

    async def create(
        self, dto: CreateRecurringRuleDTO, conn: Optional[asyncpg.Connection] = None
    ) -> RecurringRule:
        query = """
            INSERT INTO recurring_rules (
                name, amount, currency, operation_type, payment_type,
                category_id, user_id, description, frequency, end_date
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
            RETURNING id, name, amount, currency, operation_type, payment_type,
                      category_id, user_id, description, frequency, end_date,
                      created_at, updated_at, deleted_at
        """
        record = await self.fetch_one(
            query,
            dto.name, dto.amount, dto.currency, dto.operation_type,
            dto.payment_type, dto.category_id, dto.user_id,
            dto.description, dto.frequency, dto.end_date,
            conn=conn,
        )
        return RecurringRule.from_record(dict(record))

    async def delete(
        self, rule_id: int, conn: Optional[asyncpg.Connection] = None
    ) -> bool:
        return await self.soft_delete(rule_id, conn=conn)
