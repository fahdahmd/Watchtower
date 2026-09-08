import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from watchtower.config import settings
from watchtower.database import Base, engine
from watchtower.rate_limit import limiter
from watchtower.routers import auth, dashboard, watches
from watchtower.scheduler import create_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("watchtower")

_DEV_SECRET = "changeme-dev-only-not-a-real-secret"


def _check_production_safety() -> None:
    """Refuse to start in production with a default/placeholder secret —
    this is the kind of mistake that quietly ships and stays broken."""
    if settings.env == "production" and settings.jwt_secret == _DEV_SECRET:
        raise RuntimeError(
            "WATCHTOWER_JWT_SECRET is still the development placeholder. "
            "Set a real secret before running with ENV=production."
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    _check_production_safety()
    Base.metadata.create_all(bind=engine)  # fine for this project's scale; use Alembic for larger schemas

    scheduler = create_scheduler()
    scheduler.start()
    logger.info("Scheduler started — polling every %ss", settings.scheduler_poll_seconds)

    yield

    scheduler.shutdown(wait=False)


app = FastAPI(title="Watchtower", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.mount("/static", StaticFiles(directory="src/watchtower/static"), name="static")

app.include_router(auth.router)
app.include_router(watches.router)
app.include_router(dashboard.router)
