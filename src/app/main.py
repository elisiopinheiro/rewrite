"""M4W internal API application."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.m4w.router import router as m4w_router
from app.api.problem import register_exception_handlers
from app.core.config import settings
from app.core.db import engine
from app.core.logging import configure_logging
from app.core.metrics import setup_metrics


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    yield
    engine.dispose()


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title="Clusters Metadata API",
        description="Canonical API for managed-cluster metadata.",
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )

    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(m4w_router)
    setup_metrics(app, service_name="clusters-metadata-api")

    return app


app = create_app()
