from typing import Any

from sqlalchemy import Boolean, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

SEASONS = ("winter", "spring", "summer", "fall")
RECURRENCE_TIERS = ("none", "treat", "regular", "staple")


class Meal(TimestampMixin, Base):
    __tablename__ = "meals"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    meal_type: Mapped[str] = mapped_column(String(30), default="dinner", nullable=False)
    complexity: Mapped[str] = mapped_column(String(20), default="intermediate", nullable=False)
    recurrence_tier: Mapped[str] = mapped_column(String(20), default="regular", nullable=False)
    dietary_exclusions: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    source_note: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    source_url: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    agent_sourced: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    tag_links: Mapped[list["MealTagLink"]] = relationship(
        back_populates="meal",
        cascade="all, delete-orphan",
    )
    seasonal_recurrence_overrides: Mapped[list["MealSeasonalRecurrenceOverride"]] = relationship(
        back_populates="meal",
        cascade="all, delete-orphan",
    )


class MealTag(TimestampMixin, Base):
    __tablename__ = "meal_tags"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_meal_tags_user_id_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(60), nullable=False)


class MealTagLink(Base):
    __tablename__ = "meal_tag_links"

    meal_id: Mapped[int] = mapped_column(ForeignKey("meals.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("meal_tags.id", ondelete="CASCADE"), primary_key=True)

    meal: Mapped[Meal] = relationship(back_populates="tag_links")
    tag: Mapped[MealTag] = relationship()


class MealSeasonalRecurrenceOverride(Base):
    __tablename__ = "meal_seasonal_recurrence_overrides"

    meal_id: Mapped[int] = mapped_column(ForeignKey("meals.id", ondelete="CASCADE"), primary_key=True)
    season: Mapped[str] = mapped_column(String(20), primary_key=True)
    recurrence_tier: Mapped[str] = mapped_column(String(20), nullable=False)

    meal: Mapped[Meal] = relationship(back_populates="seasonal_recurrence_overrides")
