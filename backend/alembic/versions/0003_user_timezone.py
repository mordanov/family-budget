"""add timezone to users

Revision ID: 0003_user_timezone
Revises: 0002_payment_methods
Create Date: 2026-04-03 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "0003_user_timezone"
down_revision: Union[str, None] = "0002_payment_methods"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("timezone", sa.String(length=50), nullable=False, server_default="UTC"),
    )


def downgrade() -> None:
    op.drop_column("users", "timezone")
