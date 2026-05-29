"""Partner external API application."""

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.partner.router import router as partner_router
from app.core.config import settings
from app.core.logging import configure_logging


def create_partner_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title="Clusters Metadata Partner API",
        description="Read-only API for external partner consumers (SCP, CF, SOLAR).",
        version=settings.APP_VERSION,
    )

    app.include_router(health_router)
    app.include_router(partner_router)

    return app


app = create_partner_app()
