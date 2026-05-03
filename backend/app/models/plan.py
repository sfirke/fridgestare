from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class WeeklyPlan(TimestampMixin, Base):
    __tablename__ = "weekly_plans"
    __table_args__ = (UniqueConstraint("user_id", "week_start_date", name="uq_weekly_plans_user_week"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    week_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False)
    generation_source: Mapped[str] = mapped_column(String(30), default="manual", nullable=False)
    planner_explanation: Mapped[str] = mapped_column(Text, default="", nullable=False)

    slots: Mapped[list["PlanSlot"]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="PlanSlot.slot_order",
    )


class DiscoveredRecipeCandidate(Base):
    __tablename__ = "discovered_recipe_candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    complexity: Mapped[str] = mapped_column(String(20), default="intermediate", nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, default="", nullable=False)
    accepted_meal_id: Mapped[int | None] = mapped_column(ForeignKey("meals.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class PlanSlot(Base):
    __tablename__ = "plan_slots"
    __table_args__ = (UniqueConstraint("plan_id", "slot_date", name="uq_plan_slots_plan_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("weekly_plans.id", ondelete="CASCADE"), index=True)
    slot_date: Mapped[date] = mapped_column(Date, nullable=False)
    slot_order: Mapped[int] = mapped_column(nullable=False)
    slot_type: Mapped[str] = mapped_column(String(30), default="meal", nullable=False)
    meal_id: Mapped[int | None] = mapped_column(ForeignKey("meals.id", ondelete="SET NULL"))
    discovered_candidate_id: Mapped[int | None] = mapped_column(
        ForeignKey("discovered_recipe_candidates.id", ondelete="SET NULL")
    )
    title_snapshot: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    notes_snapshot: Mapped[str] = mapped_column(Text, default="", nullable=False)
    selection_reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    outcome_status: Mapped[str | None] = mapped_column(String(20))
    outcome_logged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    plan: Mapped[WeeklyPlan] = relationship(back_populates="slots")
