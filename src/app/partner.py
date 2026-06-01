"""Partner external API application."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.partner.router import router as partner_router
from app.api.problem import register_exception_handlers
from app.core.config import settings
from app.core.db import engine
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    yield
    engine.dispose()


def create_partner_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title="Clusters Metadata Partner API",
        description="Read-only API for external partner consumers (SCP, CF, SOLAR).",
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )

    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(partner_router)

    return app


app = create_partner_app()
