import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.services.scheduler import initialize_scheduler

settings = get_settings()

app_logger = logging.getLogger("app")
if not app_logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s [%(name)s] %(message)s"))
    app_logger.addHandler(handler)
app_logger.setLevel(settings.log_level.upper())
app_logger.propagate = False


@asynccontextmanager
async def lifespan(_: FastAPI):
    app_logger.info(
        "Starting %s in %s mode (scheduler=%s, mailgun=%s, openrouter=%s, tavily=%s).",
        settings.app_name,
        settings.app_env,
        "on" if settings.scheduler_enabled else "off",
        "configured" if settings.mailgun_configured else "mock",
        "configured" if settings.openrouter_api_key.strip() else "fallback",
        "configured" if settings.tavily_api_key.strip() else "fallback",
    )
    scheduler = initialize_scheduler()
    if scheduler is not None:
        scheduler.start()
    try:
        yield
    finally:
        if scheduler is not None:
            scheduler.shutdown(wait=False)


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
    docs_url=settings.docs_url,
    redoc_url=None,
    openapi_url=settings.openapi_url,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/")
def root() -> dict[str, str]:
    payload = {"name": settings.app_name}
    if settings.docs_url:
        payload["docs"] = settings.docs_url
    return payload
