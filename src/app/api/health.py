"""Shared liveness and readiness endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.core.db import database_is_available

router = APIRouter(tags=["health"])


@router.get("/healthz", include_in_schema=False)
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz", include_in_schema=False)
def readinesscheck() -> dict[str, str]:
    if not database_is_available():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")

    return {"status": "ready"}
