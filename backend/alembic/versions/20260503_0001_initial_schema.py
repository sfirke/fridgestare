"""initial schema

Revision ID: 20260503_0001
Revises:
Create Date: 2026-05-03 00:00:01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260503_0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="UTC"),
        sa.Column("week_starts_on", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "user_preferences",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("novel_meal_ratio", sa.Float(), nullable=False, server_default="0.15"),
        sa.Column("takeout_frequency_per_week", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("allow_simple", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("allow_intermediate", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("allow_complex", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("planning_guidance_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("dietary_notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("email_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("email_day_of_week", sa.Integer(), nullable=False, server_default="6"),
        sa.Column("email_local_time", sa.Time(), nullable=False, server_default="09:00:00"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "recurring_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("rule_type", sa.String(length=50), nullable=False),
        sa.Column("rule_payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "id", name="uq_recurring_rule_user_id_id"),
    )
    op.create_index("ix_recurring_rules_user_id", "recurring_rules", ["user_id"], unique=False)

    op.create_table(
        "meals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("meal_type", sa.String(length=30), nullable=False, server_default="dinner"),
        sa.Column("complexity", sa.String(length=20), nullable=False, server_default="intermediate"),
        sa.Column("recurrence_tier", sa.String(length=20), nullable=False, server_default="regular"),
        sa.Column("seasonality_mode", sa.String(length=20), nullable=False, server_default="balanced"),
        sa.Column("dietary_exclusions", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("source_note", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("source_url", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("agent_sourced", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_meals_user_id", "meals", ["user_id"], unique=False)

    op.create_table(
        "meal_tags",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=60), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "name", name="uq_meal_tags_user_id_name"),
    )
    op.create_index("ix_meal_tags_user_id", "meal_tags", ["user_id"], unique=False)

    op.create_table(
        "meal_tag_links",
        sa.Column("meal_id", sa.Integer(), sa.ForeignKey("meals.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", sa.Integer(), sa.ForeignKey("meal_tags.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "meal_season_preferences",
        sa.Column("meal_id", sa.Integer(), sa.ForeignKey("meals.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("season", sa.String(length=20), primary_key=True),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1.0"),
    )

    op.create_table(
        "weekly_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("week_start_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="draft"),
        sa.Column("generation_source", sa.String(length=30), nullable=False, server_default="manual"),
        sa.Column("planner_explanation", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "week_start_date", name="uq_weekly_plans_user_week"),
    )
    op.create_index("ix_weekly_plans_user_id", "weekly_plans", ["user_id"], unique=False)

    op.create_table(
        "discovered_recipe_candidates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("source_url", sa.String(length=500), nullable=False),
        sa.Column("complexity", sa.String(length=20), nullable=False, server_default="intermediate"),
        sa.Column("reasoning", sa.Text(), nullable=False, server_default=""),
        sa.Column("accepted_meal_id", sa.Integer(), sa.ForeignKey("meals.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_discovered_recipe_candidates_user_id",
        "discovered_recipe_candidates",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "plan_slots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("weekly_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("slot_date", sa.Date(), nullable=False),
        sa.Column("slot_order", sa.Integer(), nullable=False),
        sa.Column("slot_type", sa.String(length=30), nullable=False, server_default="meal"),
        sa.Column("meal_id", sa.Integer(), sa.ForeignKey("meals.id", ondelete="SET NULL"), nullable=True),
        sa.Column(
            "discovered_candidate_id",
            sa.Integer(),
            sa.ForeignKey("discovered_recipe_candidates.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title_snapshot", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("notes_snapshot", sa.Text(), nullable=False, server_default=""),
        sa.Column("selection_reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("outcome_status", sa.String(length=20), nullable=True),
        sa.Column("outcome_logged_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("plan_id", "slot_date", name="uq_plan_slots_plan_date"),
    )
    op.create_index("ix_plan_slots_plan_id", "plan_slots", ["plan_id"], unique=False)

    op.create_table(
        "activity_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("weekly_plans.id", ondelete="CASCADE"), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("actor_type", sa.String(length=30), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("undo_payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_activity_log_user_id", "activity_log", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_activity_log_user_id", table_name="activity_log")
    op.drop_table("activity_log")
    op.drop_index("ix_plan_slots_plan_id", table_name="plan_slots")
    op.drop_table("plan_slots")
    op.drop_index("ix_discovered_recipe_candidates_user_id", table_name="discovered_recipe_candidates")
    op.drop_table("discovered_recipe_candidates")
    op.drop_index("ix_weekly_plans_user_id", table_name="weekly_plans")
    op.drop_table("weekly_plans")
    op.drop_table("meal_season_preferences")
    op.drop_table("meal_tag_links")
    op.drop_index("ix_meal_tags_user_id", table_name="meal_tags")
    op.drop_table("meal_tags")
    op.drop_index("ix_meals_user_id", table_name="meals")
    op.drop_table("meals")
    op.drop_index("ix_recurring_rules_user_id", table_name="recurring_rules")
    op.drop_table("recurring_rules")
    op.drop_table("user_preferences")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
