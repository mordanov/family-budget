"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    operation_type_enum = postgresql.ENUM(
        "income", "expense", name="operation_type", create_type=False
    )
    payment_type_enum = postgresql.ENUM(
        "cash", "card", "bank_transfer", "other", name="payment_type", create_type=False
    )

    # Users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # Categories
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("color", sa.String(7), nullable=True),
        sa.Column("icon", sa.String(50), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_categories_id", "categories", ["id"])
    op.create_index("ix_categories_name", "categories", ["name"], unique=True)

    # Enums
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'operation_type') THEN
                CREATE TYPE operation_type AS ENUM ('income', 'expense');
            END IF;
        END
        $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'payment_type') THEN
                CREATE TYPE payment_type AS ENUM ('cash', 'card', 'bank_transfer', 'other');
            END IF;
        END
        $$;
        """
    )

    # Operations
    op.create_table(
        "operations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="EUR"),
        sa.Column("type", operation_type_enum, nullable=False),
        sa.Column("payment_type", payment_type_enum, nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_recurring", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("recurring_end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("operation_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_operations_id", "operations", ["id"])
    op.create_index("ix_operations_type", "operations", ["type"])
    op.create_index("ix_operations_operation_date", "operations", ["operation_date"])
    op.create_index("ix_operations_user_id", "operations", ["user_id"])
    op.create_index("ix_operations_category_id", "operations", ["category_id"])

    # Attachments
    op.create_table(
        "attachments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("operation_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["operation_id"], ["operations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_attachments_id", "attachments", ["id"])
    op.create_index("ix_attachments_operation_id", "attachments", ["operation_id"])

    # Monthly balances
    op.create_table(
        "monthly_balances",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("total_income", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("total_expense", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("opening_balance", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("closing_balance", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("is_manually_adjusted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("manual_opening_balance", sa.Numeric(12, 2), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("year", "month", name="uq_monthly_balance_year_month"),
    )
    op.create_index("ix_monthly_balances_id", "monthly_balances", ["id"])
    op.create_index("ix_monthly_balances_year", "monthly_balances", ["year"])
    op.create_index("ix_monthly_balances_month", "monthly_balances", ["month"])


def downgrade() -> None:
    op.drop_table("monthly_balances")
    op.drop_table("attachments")
    op.drop_table("operations")
    op.execute("DROP TYPE IF EXISTS payment_type")
    op.execute("DROP TYPE IF EXISTS operation_type")
    op.drop_table("categories")
    op.drop_table("users")
