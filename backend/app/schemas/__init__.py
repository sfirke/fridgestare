from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.discovery import DiscoveryAcceptRequest, DiscoveryCandidateOut, DiscoverySuggestRequest
from app.schemas.email import EmailPreviewOut, SendEmailResponse
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.meal import BulkFastAddRequest, MealCreate, MealOut, MealUpdate, TagSuggestionOut
from app.schemas.plan import (
    GeneratePlanRequest,
    MoveSlotRequest,
    OutcomeStatusUpdate,
    PlanOut,
    PlanSlotOut,
    RerollSlotRequest,
    SetSlotRequest,
)
from app.schemas.user import (
    MeResponse,
    RecurringRuleIn,
    RecurringRuleOut,
    ScheduleRulesUpdate,
    UserOut,
    UserPreferencesOut,
    UserPreferencesUpdate,
)

__all__ = [
    "BulkFastAddRequest",
    "ChatRequest",
    "ChatResponse",
    "DiscoveryAcceptRequest",
    "DiscoveryCandidateOut",
    "DiscoverySuggestRequest",
    "EmailPreviewOut",
    "GeneratePlanRequest",
    "LoginRequest",
    "LoginResponse",
    "MealCreate",
    "MealOut",
    "MealUpdate",
    "MeResponse",
    "MoveSlotRequest",
    "OutcomeStatusUpdate",
    "PlanOut",
    "PlanSlotOut",
    "RecurringRuleIn",
    "RecurringRuleOut",
    "RerollSlotRequest",
    "ScheduleRulesUpdate",
    "SetSlotRequest",
    "SendEmailResponse",
    "TagSuggestionOut",
    "UserOut",
    "UserPreferencesOut",
    "UserPreferencesUpdate",
]

