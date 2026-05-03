from fastapi import APIRouter

from app.api.routes import auth, health, meals, plans, tags, users

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(meals.router, prefix="/meals", tags=["meals"])
api_router.include_router(plans.router, prefix="/plans", tags=["plans"])
api_router.include_router(tags.router, prefix="/tags", tags=["tags"])
api_router.include_router(users.router, tags=["users"])
api_router.include_router(health.router, tags=["health"])


