from pydantic import BaseModel

from app.schemas.plan import PlanOut


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    plan: PlanOut
    explanation: str
