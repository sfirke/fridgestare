from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MealCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    notes: str = ""
    complexity: str = "intermediate"
    recurrence_tier: str = "regular"
    seasonality_mode: str = "balanced"
    dietary_exclusions: list[str] = Field(default_factory=list)
    source_note: str = ""
    source_url: str = ""
    tags: list[str] = Field(default_factory=list)


class BulkFastAddRequest(BaseModel):
    meals: list[MealCreate]


class MealUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    notes: str | None = None
    complexity: str | None = None
    recurrence_tier: str | None = None
    seasonality_mode: str | None = None
    dietary_exclusions: list[str] | None = None
    source_note: str | None = None
    source_url: str | None = None
    tags: list[str] | None = None
    is_archived: bool | None = None


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
    recurrence_tier: str
    seasonality_mode: str
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
