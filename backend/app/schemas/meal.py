from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

SeasonName = Literal["winter", "spring", "summer", "fall"]
RecurrenceTier = Literal["none", "treat", "regular", "staple"]


class MealSeasonalRecurrenceOverride(BaseModel):
    season: SeasonName
    recurrence_tier: RecurrenceTier


def _validate_unique_seasons(
    overrides: list[MealSeasonalRecurrenceOverride],
) -> list[MealSeasonalRecurrenceOverride]:
    seasons = [override.season for override in overrides]
    if len(seasons) != len(set(seasons)):
        raise ValueError("Seasonal recurrence overrides must use each season at most once.")
    return overrides


class MealCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    notes: str = ""
    complexity: str = "intermediate"
    recurrence_tier: RecurrenceTier = "regular"
    seasonal_recurrence_overrides: list[MealSeasonalRecurrenceOverride] = Field(
        default_factory=list
    )
    dietary_exclusions: list[str] = Field(default_factory=list)
    source_note: str = ""
    source_url: str = ""
    tags: list[str] = Field(default_factory=list)

    _validate_override_seasons = field_validator("seasonal_recurrence_overrides")(
        _validate_unique_seasons
    )


class BulkFastAddRequest(BaseModel):
    meals: list[MealCreate]


class MealUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    notes: str | None = None
    complexity: str | None = None
    recurrence_tier: RecurrenceTier | None = None
    seasonal_recurrence_overrides: list[MealSeasonalRecurrenceOverride] | None = None
    dietary_exclusions: list[str] | None = None
    source_note: str | None = None
    source_url: str | None = None
    tags: list[str] | None = None
    is_archived: bool | None = None

    _validate_override_seasons = field_validator("seasonal_recurrence_overrides")(
        _validate_unique_seasons
    )


class MealTagOut(BaseModel):
    id: int
    name: str


class MealOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    notes: str
    meal_type: str
    complexity: str
    recurrence_tier: RecurrenceTier
    seasonal_recurrence_overrides: list[MealSeasonalRecurrenceOverride]
    dietary_exclusions: list[str]
    source_note: str
    source_url: str
    agent_sourced: bool
    is_archived: bool
    tags: list[MealTagOut]
    created_at: datetime
    updated_at: datetime


class TagSuggestionOut(BaseModel):
    name: str
