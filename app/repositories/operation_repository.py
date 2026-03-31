from typing import Optional
from decimal import Decimal
from datetime import datetime
import asyncpg

from app.repositories.base_repository import BaseRepository
from app.models.operation import Operation, CreateOperationDTO, UpdateOperationDTO, OperationFilter


_SELECT = """
    SELECT
        o.id, o.amount, o.currency, o.operation_type, o.payment_type,
        o.category_id, o.user_id, o.operation_date, o.description,
        o.recurring_rule_id, o.forecast_end_date, o.is_recurring,
        o.created_at, o.updated_at, o.deleted_at,
        c.name AS category_name,
        u.name AS user_name
    FROM operations o
    LEFT JOIN categories c ON c.id = o.category_id
    LEFT JOIN users u ON u.id = o.user_id
"""


class OperationRepository(BaseRepository):
    def __init__(self):
        super().__init__("operations")

    def _build_filter(
        self, f: OperationFilter, start_idx: int = 1
    ) -> tuple[str, list]:
        clauses = ["o.deleted_at IS NULL"]
        values = []
        idx = start_idx

        if f.date_from:
            clauses.append(f"o.operation_date >= ${idx}")
            values.append(f.date_from)
            idx += 1
        if f.date_to:
            clauses.append(f"o.operation_date <= ${idx}")
            values.append(f.date_to)
            idx += 1
        if f.operation_type:
            clauses.append(f"o.operation_type = ${idx}")
            values.append(f.operation_type.value)
            idx += 1
        if f.payment_type:
            clauses.append(f"o.payment_type = ${idx}")
            values.append(f.payment_type.value)
            idx += 1
        if f.category_id:
            clauses.append(f"o.category_id = ${idx}")
            values.append(f.category_id)
            idx += 1
        if f.user_id:
            clauses.append(f"o.user_id = ${idx}")
            values.append(f.user_id)
            idx += 1
        if f.currency:
            clauses.append(f"o.currency = ${idx}")
            values.append(f.currency.value)
            idx += 1
        if f.is_recurring is not None:
            clauses.append(f"o.is_recurring = ${idx}")
            values.append(f.is_recurring)
            idx += 1
        if f.search:
            clauses.append(f"o.description ILIKE ${idx}")
            values.append(f"%{f.search}%")
            idx += 1

        return " AND ".join(clauses), values

    async def get_by_id(
        self, op_id: int, conn: Optional[asyncpg.Connection] = None
    ) -> Optional[Operation]:
        query = _SELECT + " WHERE o.id = $1 AND o.deleted_at IS NULL"
        record = await self.fetch_one(query, op_id, conn=conn)
        return Operation.from_record(dict(record)) if record else None

    async def get_many(
        self,
        f: OperationFilter,
        limit: int = 100,
        offset: int = 0,
        conn: Optional[asyncpg.Connection] = None,
    ) -> list[Operation]:
        where, values = self._build_filter(f)
        values.extend([limit, offset])
        lim_idx = len(values) - 1
        off_idx = len(values)

        query = (
            _SELECT
            + f" WHERE {where}"
            + f" ORDER BY o.operation_date DESC, o.id DESC"
            + f" LIMIT ${lim_idx} OFFSET ${off_idx}"
        )
        records = await self.fetch_many(query, *values, conn=conn)
        return [Operation.from_record(dict(r)) for r in records]

    async def count_many(
        self, f: OperationFilter, conn: Optional[asyncpg.Connection] = None
    ) -> int:
        where, values = self._build_filter(f)
        query = f"SELECT COUNT(*) FROM operations o WHERE {where}"
        return await self.fetch_val(query, *values, conn=conn) or 0

    async def create(
        self, dto: CreateOperationDTO, conn: Optional[asyncpg.Connection] = None
    ) -> Operation:
        query = """
            INSERT INTO operations (
                amount, currency, operation_type, payment_type,
                category_id, user_id, operation_date, description,
                recurring_rule_id, forecast_end_date, is_recurring
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
            RETURNING id
        """
        op_id = await self.fetch_val(
            query,
            dto.amount, dto.currency.value, dto.operation_type.value,
            dto.payment_type.value, dto.category_id, dto.user_id,
            dto.operation_date, dto.description, dto.recurring_rule_id,
            dto.forecast_end_date, dto.is_recurring,
            conn=conn,
        )
        return await self.get_by_id(op_id, conn=conn)

    async def update(
        self, op_id: int, dto: UpdateOperationDTO, conn: Optional[asyncpg.Connection] = None
    ) -> Optional[Operation]:
        fields = []
        values = []
        idx = 1

        mapping = {
            "amount": dto.amount,
            "currency": dto.currency.value if dto.currency else None,
            "operation_type": dto.operation_type.value if dto.operation_type else None,
            "payment_type": dto.payment_type.value if dto.payment_type else None,
            "category_id": dto.category_id,
            "user_id": dto.user_id,
            "operation_date": dto.operation_date,
            "description": dto.description,
            "recurring_rule_id": dto.recurring_rule_id,
            "forecast_end_date": dto.forecast_end_date,
            "is_recurring": dto.is_recurring,
        }

        for col, val in mapping.items():
            if val is not None:
                fields.append(f"{col} = ${idx}")
                values.append(val)
                idx += 1

        if not fields:
            return await self.get_by_id(op_id, conn=conn)

        fields.append("updated_at = NOW()")
        values.append(op_id)

        query = f"""
            UPDATE operations SET {', '.join(fields)}
            WHERE id = ${idx} AND deleted_at IS NULL
            RETURNING id
        """
        result_id = await self.fetch_val(query, *values, conn=conn)
        return await self.get_by_id(result_id, conn=conn) if result_id else None

    async def delete(
        self, op_id: int, conn: Optional[asyncpg.Connection] = None
    ) -> bool:
        return await self.soft_delete(op_id, conn=conn)

    async def get_sum_by_type(
        self,
        f: OperationFilter,
        conn: Optional[asyncpg.Connection] = None,
    ) -> dict[str, Decimal]:
        where, values = self._build_filter(f)
        query = f"""
            SELECT operation_type, SUM(amount) as total
            FROM operations o
            WHERE {where}
            GROUP BY operation_type
        """
        records = await self.fetch_many(query, *values, conn=conn)
        return {r["operation_type"]: Decimal(str(r["total"])) for r in records}

    async def get_sum_by_category(
        self,
        f: OperationFilter,
        conn: Optional[asyncpg.Connection] = None,
    ) -> list[dict]:
        where, values = self._build_filter(f)
        query = f"""
            SELECT c.name AS category_name, o.operation_type,
                   SUM(o.amount) AS total, COUNT(*) AS count
            FROM operations o
            LEFT JOIN categories c ON c.id = o.category_id
            WHERE {where}
            GROUP BY c.name, o.operation_type
            ORDER BY total DESC
        """
        records = await self.fetch_many(query, *values, conn=conn)
        return [dict(r) for r in records]

    async def get_sum_by_user(
        self,
        f: OperationFilter,
        conn: Optional[asyncpg.Connection] = None,
    ) -> list[dict]:
        where, values = self._build_filter(f)
        query = f"""
            SELECT u.name AS user_name, o.operation_type,
                   SUM(o.amount) AS total, COUNT(*) AS count
            FROM operations o
            LEFT JOIN users u ON u.id = o.user_id
            WHERE {where}
            GROUP BY u.name, o.operation_type
            ORDER BY total DESC
        """
        records = await self.fetch_many(query, *values, conn=conn)
        return [dict(r) for r in records]

    async def get_sum_by_payment_type(
        self,
        f: OperationFilter,
        conn: Optional[asyncpg.Connection] = None,
    ) -> list[dict]:
        where, values = self._build_filter(f)
        query = f"""
            SELECT o.payment_type, o.operation_type,
                   SUM(o.amount) AS total, COUNT(*) AS count
            FROM operations o
            WHERE {where}
            GROUP BY o.payment_type, o.operation_type
            ORDER BY total DESC
        """
        records = await self.fetch_many(query, *values, conn=conn)
        return [dict(r) for r in records]

    async def get_monthly_totals(
        self,
        year: Optional[int] = None,
        conn: Optional[asyncpg.Connection] = None,
    ) -> list[dict]:
        if year:
            query = """
                SELECT
                    EXTRACT(YEAR FROM operation_date)::int AS year,
                    EXTRACT(MONTH FROM operation_date)::int AS month,
                    operation_type,
                    SUM(amount) AS total
                FROM operations
                WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM operation_date) = $1
                GROUP BY year, month, operation_type
                ORDER BY year, month
            """
            records = await self.fetch_many(query, year, conn=conn)
        else:
            query = """
                SELECT
                    EXTRACT(YEAR FROM operation_date)::int AS year,
                    EXTRACT(MONTH FROM operation_date)::int AS month,
                    operation_type,
                    SUM(amount) AS total
                FROM operations
                WHERE deleted_at IS NULL
                GROUP BY year, month, operation_type
                ORDER BY year, month
            """
            records = await self.fetch_many(query, conn=conn)
        return [dict(r) for r in records]

    async def get_recurring(
        self, conn: Optional[asyncpg.Connection] = None
    ) -> list[Operation]:
        f = OperationFilter(is_recurring=True)
        return await self.get_many(f, limit=1000, conn=conn)
