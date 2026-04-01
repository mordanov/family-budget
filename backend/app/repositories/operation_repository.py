from datetime import datetime
from decimal import Decimal
from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.operation import Operation, OperationType
from app.models.category import Category
from app.models.payment_method import PaymentMethod
from app.models.user import User
from app.repositories.base import BaseRepository


class OperationRepository(BaseRepository[Operation]):
    def __init__(self, db: AsyncSession):
        super().__init__(Operation, db)

    def _base_query(self):
        return (
            select(Operation)
            .where(Operation.deleted_at == None)
            .options(
                selectinload(Operation.category),
                selectinload(Operation.user),
                selectinload(Operation.payment_method),
                selectinload(Operation.attachments),
            )
        )

    async def get_by_id_with_relations(self, id: int) -> Operation | None:
        result = await self.db.execute(self._base_query().where(Operation.id == id))
        return result.scalar_one_or_none()

    async def get_filtered(
        self,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        type: OperationType | None = None,
        payment_type=None,
        category_id: int | None = None,
        user_id: int | None = None,
        is_recurring: bool | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Operation], int]:
        q = self._base_query()

        if date_from:
            q = q.where(Operation.operation_date >= date_from)
        if date_to:
            q = q.where(Operation.operation_date <= date_to)
        if type:
            q = q.where(Operation.type == type)
        if payment_type:
            q = q.where(Operation.payment_type == payment_type)
        if category_id:
            q = q.where(Operation.category_id == category_id)
        if user_id:
            q = q.where(Operation.user_id == user_id)
        if is_recurring is not None:
            q = q.where(Operation.is_recurring == is_recurring)

        # Count
        count_q = select(func.count()).select_from(
            q.order_by(None).subquery()
        )
        total_result = await self.db.execute(count_q)
        total = total_result.scalar_one()

        # Paginate
        q = q.order_by(Operation.operation_date.desc()).offset(skip).limit(limit)
        result = await self.db.execute(q)
        return list(result.scalars().all()), total

    async def get_recurring_active(self, as_of: datetime) -> list[Operation]:
        q = self._base_query().where(
            and_(
                Operation.is_recurring == True,
                or_(
                    Operation.recurring_end_date == None,
                    Operation.recurring_end_date >= as_of,
                ),
            )
        )
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get_totals_by_period(
        self, date_from: datetime, date_to: datetime
    ) -> dict:
        q = (
            select(
                Operation.type,
                func.sum(Operation.amount).label("total"),
                func.count(Operation.id).label("count"),
            )
            .where(
                and_(
                    Operation.deleted_at == None,
                    Operation.operation_date >= date_from,
                    Operation.operation_date <= date_to,
                )
            )
            .group_by(Operation.type)
        )
        result = await self.db.execute(q)
        rows = result.all()
        out = {"income": Decimal("0"), "expense": Decimal("0")}
        for row in rows:
            out[row.type.value] = row.total or Decimal("0")
        return out

    async def get_by_category_period(
        self, date_from: datetime, date_to: datetime
    ) -> list:
        q = (
            select(
                Operation.category_id,
                Category.name.label("category_name"),
                Category.color.label("category_color"),
                Operation.type,
                func.sum(Operation.amount).label("total"),
                func.count(Operation.id).label("count"),
            )
            .join(Category, Operation.category_id == Category.id)
            .where(
                and_(
                    Operation.deleted_at == None,
                    Operation.operation_date >= date_from,
                    Operation.operation_date <= date_to,
                )
            )
            .group_by(Operation.category_id, Category.name, Category.color, Operation.type)
            .order_by(Category.name)
        )
        result = await self.db.execute(q)
        return result.all()

    async def get_by_user_period(self, date_from: datetime, date_to: datetime) -> list:
        q = (
            select(
                Operation.user_id,
                User.name.label("user_name"),
                Operation.type,
                func.sum(Operation.amount).label("total"),
                func.count(Operation.id).label("count"),
            )
            .join(User, Operation.user_id == User.id)
            .where(
                and_(
                    Operation.deleted_at == None,
                    Operation.operation_date >= date_from,
                    Operation.operation_date <= date_to,
                )
            )
            .group_by(Operation.user_id, User.name, Operation.type)
        )
        result = await self.db.execute(q)
        return result.all()

    async def get_by_payment_type_period(
        self, date_from: datetime, date_to: datetime
    ) -> list:
        q = (
            select(
                Operation.payment_type,
                PaymentMethod.name.label("payment_method_name"),
                Operation.type,
                func.sum(Operation.amount).label("total"),
                func.count(Operation.id).label("count"),
            )
            .join(PaymentMethod, Operation.payment_method_id == PaymentMethod.id)
            .where(
                and_(
                    Operation.deleted_at == None,
                    Operation.operation_date >= date_from,
                    Operation.operation_date <= date_to,
                )
            )
            .group_by(Operation.payment_type, PaymentMethod.name, Operation.type)
        )
        result = await self.db.execute(q)
        return result.all()

    async def get_balance_before(self, date_from: datetime) -> Decimal:
        q = (
            select(
                func.coalesce(
                    func.sum(
                        (Operation.amount)
                        * case((Operation.type == OperationType.income, 1), else_=-1)
                    ),
                    0,
                )
            )
            .where(
                and_(
                    Operation.deleted_at == None,
                    Operation.operation_date < date_from,
                )
            )
        )
        result = await self.db.execute(q)
        return Decimal(result.scalar_one() or 0)

    async def get_daily_net(self, date_from: datetime, date_to: datetime) -> list:
        q = (
            select(
                func.date(Operation.operation_date).label("day"),
                Operation.type,
                func.sum(Operation.amount).label("total"),
            )
            .where(
                and_(
                    Operation.deleted_at == None,
                    Operation.operation_date >= date_from,
                    Operation.operation_date <= date_to,
                )
            )
            .group_by(func.date(Operation.operation_date), Operation.type)
            .order_by(func.date(Operation.operation_date))
        )
        result = await self.db.execute(q)
        return result.all()

    async def get_monthly_trend(
        self, date_from: datetime, date_to: datetime
    ) -> list:
        q = (
            select(
                func.extract("year", Operation.operation_date).label("year"),
                func.extract("month", Operation.operation_date).label("month"),
                Operation.type,
                func.sum(Operation.amount).label("total"),
            )
            .where(
                and_(
                    Operation.deleted_at == None,
                    Operation.operation_date >= date_from,
                    Operation.operation_date <= date_to,
                )
            )
            .group_by(
                func.extract("year", Operation.operation_date),
                func.extract("month", Operation.operation_date),
                Operation.type,
            )
            .order_by(
                func.extract("year", Operation.operation_date),
                func.extract("month", Operation.operation_date),
            )
        )
        result = await self.db.execute(q)
        return result.all()

    async def soft_delete(self, operation: Operation) -> Operation:
        from datetime import timezone
        operation.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
        return operation
