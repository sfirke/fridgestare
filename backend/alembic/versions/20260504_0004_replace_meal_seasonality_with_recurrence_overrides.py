"""replace meal seasonality with seasonal recurrence overrides

Revision ID: 20260504_0004
Revises: 20260503_0003
Create Date: 2026-05-04 13:10:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260504_0004"
down_revision: str | None = "20260503_0003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = set(inspector.get_table_names())

    if "meals" in table_names:
        meal_columns = {column["name"] for column in inspector.get_columns("meals")}
        if "seasonality_mode" in meal_columns:
            with op.batch_alter_table("meals") as batch_op:
                batch_op.drop_column("seasonality_mode")

    if "meal_seasonal_recurrence_overrides" not in table_names:
        op.create_table(
            "meal_seasonal_recurrence_overrides",
            sa.Column("meal_id", sa.Integer(), sa.ForeignKey("meals.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("season", sa.String(length=20), primary_key=True),
            sa.Column("recurrence_tier", sa.String(length=20), nullable=False),
        )

    if "meal_season_preferences" in table_names:
        op.drop_table("meal_season_preferences")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = set(inspector.get_table_names())

    if "meal_seasonal_recurrence_overrides" in table_names:
        op.drop_table("meal_seasonal_recurrence_overrides")

    if "meal_season_preferences" not in table_names:
        op.create_table(
            "meal_season_preferences",
            sa.Column("meal_id", sa.Integer(), sa.ForeignKey("meals.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("season", sa.String(length=20), primary_key=True),
            sa.Column("weight", sa.Float(), nullable=False, server_default="1.0"),
        )

    if "meals" in table_names:
        meal_columns = {column["name"] for column in inspector.get_columns("meals")}
        if "seasonality_mode" not in meal_columns:
            with op.batch_alter_table("meals") as batch_op:
                batch_op.add_column(
                    sa.Column("seasonality_mode", sa.String(length=20), nullable=False, server_default="balanced")
                )