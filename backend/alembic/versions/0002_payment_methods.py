"""payment methods dictionary

Revision ID: 0002_payment_methods
Revises: 0001_initial
Create Date: 2026-04-02 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "0002_payment_methods"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "payment_methods",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payment_methods_id", "payment_methods", ["id"])
    op.create_index("ix_payment_methods_key", "payment_methods", ["key"], unique=True)

    op.execute(
        """
        INSERT INTO payment_methods (key, name)
        VALUES
          ('cash', 'Cash'),
          ('card', 'Card'),
          ('bank_transfer', 'Bank Transfer'),
          ('other', 'Other')
        ON CONFLICT (key) DO NOTHING;
        """
    )

    op.add_column("operations", sa.Column("payment_method_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_operations_payment_method_id",
        "operations",
        "payment_methods",
        ["payment_method_id"],
        ["id"],
    )
    op.create_index("ix_operations_payment_method_id", "operations", ["payment_method_id"])

    op.execute(
        """
        UPDATE operations o
        SET payment_method_id = pm.id
        FROM payment_methods pm
        WHERE pm.key = o.payment_type::text;
        """
    )

    op.alter_column("operations", "payment_method_id", nullable=False)


def downgrade() -> None:
    op.drop_index("ix_operations_payment_method_id", table_name="operations")
    op.drop_constraint("fk_operations_payment_method_id", "operations", type_="foreignkey")
    op.drop_column("operations", "payment_method_id")

    op.drop_index("ix_payment_methods_key", table_name="payment_methods")
    op.drop_index("ix_payment_methods_id", table_name="payment_methods")
    op.drop_table("payment_methods")

