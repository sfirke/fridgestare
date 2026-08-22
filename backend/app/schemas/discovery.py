from datetime import datetime

from pydantic import BaseModel


class DiscoverySuggestRequest(BaseModel):
    slot_id: int | None = None
    query: str | None = None


class DiscoveryCandidateOut(BaseModel):
    id: int
    title: str
    summary: str
    source_url: str
    complexity: str
    reasoning: str
    accepted_meal_id: int | None
    created_at: datetime


class DiscoveryAcceptRequest(BaseModel):
    plan_id: int | None = None
    slot_id: int | None = None
    apply_to_plan: bool = True
