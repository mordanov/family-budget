"""add default_payment_method_id to users

Revision ID: 0005_user_default_payment_method
Revises: 0004_attachment_kitchen_sent_at
Create Date: 2026-04-25 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "0005_user_default_payment_method"
down_revision: Union[str, None] = "0004_attachment_kitchen_sent_at"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "default_payment_method_id",
            sa.Integer(),
            sa.ForeignKey("payment_methods.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "default_payment_method_id")
