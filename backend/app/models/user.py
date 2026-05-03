from datetime import time
from datetime import datetime, time
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)
    week_starts_on: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    preferences: Mapped["UserPreferences | None"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    recurring_rules: Mapped[list["RecurringRule"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    novel_meal_ratio: Mapped[float] = mapped_column(default=0.15, nullable=False)
    takeout_frequency_per_week: Mapped[float] = mapped_column(default=1.0, nullable=False)
    allow_simple: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allow_intermediate: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allow_complex: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    planning_guidance_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    dietary_notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_day_of_week: Mapped[int] = mapped_column(Integer, default=6, nullable=False)
    email_local_time: Mapped[time] = mapped_column(default=time(hour=9), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="preferences")


class RecurringRule(TimestampMixin, Base):
    __tablename__ = "recurring_rules"
    __table_args__ = (UniqueConstraint("user_id", "id", name="uq_recurring_rule_user_id_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    rule_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user: Mapped[User] = relationship(back_populates="recurring_rules")
