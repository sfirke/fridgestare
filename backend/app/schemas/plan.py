from datetime import date, datetime

from pydantic import BaseModel, Field


class GeneratePlanRequest(BaseModel):
    week_start_date: date | None = None
    force_regenerate: bool = False


class PlanSlotOut(BaseModel):
    id: int
    slot_date: date
    slot_order: int
    slot_type: str
    meal_id: int | None
    discovered_candidate_id: int | None
    title_snapshot: str
    notes_snapshot: str
    selection_reason: str
    outcome_status: str | None
    outcome_logged_at: datetime | None


class PlanOut(BaseModel):
    id: int
    week_start_date: date
    status: str
    generation_source: str
    planner_explanation: str
    slots: list[PlanSlotOut]


class RerollSlotRequest(BaseModel):
    slot_id: int


class MoveSlotRequest(BaseModel):
    source_slot_id: int
    target_slot_id: int


class SetSlotRequest(BaseModel):
    slot_id: int
    meal_id: int | None = None
    discovered_candidate_id: int | None = None
    slot_type: str = Field(default="meal")
    title_snapshot: str | None = None
    notes_snapshot: str | None = None


class OutcomeStatusUpdate(BaseModel):
    outcome_status: str | None = None
