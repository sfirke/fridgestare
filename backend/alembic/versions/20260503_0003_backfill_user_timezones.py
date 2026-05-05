"""backfill user timezone defaults

Revision ID: 20260503_0003
Revises: 20260503_0002
Create Date: 2026-05-03 23:15:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260503_0003"
down_revision: str | None = "20260503_0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    user_columns = {column["name"] for column in inspector.get_columns("users")}

    if "timezone" not in user_columns:
        op.add_column("users", sa.Column("timezone", sa.String(length=64), nullable=False, server_default="UTC"))
    if "week_starts_on" not in user_columns:
        op.add_column("users", sa.Column("week_starts_on", sa.Integer(), nullable=False, server_default="0"))

    op.execute(sa.text("UPDATE users SET timezone = 'UTC' WHERE timezone IS NULL OR TRIM(timezone) = ''"))
    op.execute(sa.text("UPDATE users SET week_starts_on = 0 WHERE week_starts_on IS NULL OR week_starts_on < 0 OR week_starts_on > 6"))


def downgrade() -> None:
    pass