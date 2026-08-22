from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.discovery import (
    DiscoveryAcceptRequest,
    DiscoveryCandidateOut,
    DiscoverySuggestRequest,
)
from app.schemas.email import EmailPreviewOut, SendEmailResponse
from app.schemas.meal import BulkFastAddRequest, MealCreate, MealOut, MealUpdate, TagSuggestionOut
from app.schemas.plan import (
    GeneratePlanRequest,
    MoveSlotRequest,
    OutcomeStatusUpdate,
    PlanOut,
    PlanSlotOut,
    PlanSummaryOut,
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
    "MeResponse",
    "MealCreate",
    "MealOut",
    "MealUpdate",
    "MoveSlotRequest",
    "OutcomeStatusUpdate",
    "PlanOut",
    "PlanSlotOut",
    "PlanSummaryOut",
    "RecurringRuleIn",
    "RecurringRuleOut",
    "RerollSlotRequest",
    "ScheduleRulesUpdate",
    "SendEmailResponse",
    "SetSlotRequest",
    "TagSuggestionOut",
    "UserOut",
    "UserPreferencesOut",
    "UserPreferencesUpdate",
]
