"""add leftovers preference

Revision ID: 20260503_0002
Revises: 20260503_0001
Create Date: 2026-05-03 00:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260503_0002"
down_revision: str | None = "20260503_0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "user_preferences",
        sa.Column("leftovers_per_week", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("user_preferences", "leftovers_per_week")