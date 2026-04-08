"""add kitchen_sent_at to attachments

Revision ID: 0004_attachment_kitchen_sent_at
Revises: 0003_user_timezone
Create Date: 2026-04-08 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "0004_attachment_kitchen_sent_at"
down_revision: Union[str, None] = "0003_user_timezone"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "attachments",
        sa.Column("kitchen_sent_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("attachments", "kitchen_sent_at")
