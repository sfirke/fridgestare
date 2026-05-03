from datetime import datetime, time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    timezone: str
    week_starts_on: int
    is_admin: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserPreferencesOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    novel_meal_ratio: float
    takeout_frequency_per_week: float
    allow_simple: bool
    allow_intermediate: bool
    allow_complex: bool
    planning_guidance_text: str
    dietary_notes: str
    email_enabled: bool
    email_day_of_week: int
    email_local_time: time
    updated_at: datetime


class UserPreferencesUpdate(BaseModel):
    novel_meal_ratio: float | None = Field(default=None, ge=0, le=1)
    takeout_frequency_per_week: float | None = Field(default=None, ge=0, le=7)
    allow_simple: bool | None = None
    allow_intermediate: bool | None = None
    allow_complex: bool | None = None
    planning_guidance_text: str | None = None
    dietary_notes: str | None = None
    email_enabled: bool | None = None
    email_day_of_week: int | None = Field(default=None, ge=0, le=6)
    email_local_time: time | None = None


class RecurringRuleIn(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    rule_type: str
    rule_payload: dict[str, Any] = Field(default_factory=dict)
    priority: int = 100
    active: bool = True


class RecurringRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    day_of_week: int
    rule_type: str
    rule_payload: dict[str, Any]
    priority: int
    active: bool
    created_at: datetime
    updated_at: datetime


class ScheduleRulesUpdate(BaseModel):
    rules: list[RecurringRuleIn]


class MeResponse(BaseModel):
    user: UserOut
    preferences: UserPreferencesOut
    recurring_rules: list[RecurringRuleOut]
