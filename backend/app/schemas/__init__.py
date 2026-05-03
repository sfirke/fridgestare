from app.schemas.auth import LoginRequest, LoginResponse
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
    "TagSuggestionOut",
    "UserOut",
    "UserPreferencesOut",
    "UserPreferencesUpdate",
]

