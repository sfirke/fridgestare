"""drop unused novel_meal_ratio preference

Revision ID: 20260823_0002
Revises: 20260822_0001
Create Date: 2026-08-23 00:00:01

The column was written by the preferences form but never read by the planner, so the
value it stored had no effect on any generated plan.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260823_0002"
down_revision: str | None = "20260822_0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("user_preferences", "novel_meal_ratio")


def downgrade() -> None:
    op.add_column(
        "user_preferences",
        sa.Column("novel_meal_ratio", sa.Double(), nullable=False, server_default="0.15"),
    )
