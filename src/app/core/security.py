"""Authentication and authorization dependencies."""

import secrets
from collections.abc import Callable
from enum import StrEnum
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.core.config import settings

security = HTTPBasic()
Credentials = Annotated[HTTPBasicCredentials, Depends(security)]


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Basic"},
    )


def _check(credentials: HTTPBasicCredentials, username: str, password: str) -> bool:
    return secrets.compare_digest(credentials.username.encode("utf8"), username.encode("utf8")) and secrets.compare_digest(
        credentials.password.encode("utf8"), password.encode("utf8")
    )


def validate_m4w_credentials(credentials: Credentials) -> str:
    """Validate credentials for the internal M4W management API."""
    if not _check(credentials, settings.BASIC_API_USERNAME, settings.BASIC_API_PASSWORD):
        raise _unauthorized()
    return credentials.username


def validate_partner_credentials(credentials: Credentials) -> str:
    """Validate credentials for the partner API (multiple users)."""
    partner_accounts = (
        (settings.BASIC_M4W_API_USERNAME, settings.BASIC_M4W_API_PASSWORD),
        (settings.BASIC_CLOUD_API_USERNAME, settings.BASIC_CLOUD_API_PASSWORD),
        (settings.BASIC_SCP_API_USERNAME, settings.BASIC_SCP_API_PASSWORD),
        (settings.BASIC_SOLAR_API_USERNAME, settings.BASIC_SOLAR_API_PASSWORD),
    )
    if not any(_check(credentials, u, p) for u, p in partner_accounts):
        raise _unauthorized()
    return credentials.username


PartnerUser = Annotated[str, Depends(validate_partner_credentials)]


class Role(StrEnum):
    M4W = "4Wheels Managed"
    CF = "Cloud Foundation"
    SCP = "Standard Cloud Platform"
    SOLAR = "Solution Landscape and Anomaly Reporter"


def _get_user_roles(username: str) -> list[Role]:
    mapping: dict[str, list[Role]] = {
        settings.BASIC_M4W_API_USERNAME: [Role.M4W],
        settings.BASIC_CLOUD_API_USERNAME: [Role.CF],
        settings.BASIC_SCP_API_USERNAME: [Role.SCP],
        settings.BASIC_SOLAR_API_USERNAME: [Role.SOLAR],
    }
    return mapping.get(username, [])


def require_roles(allowed_roles: list[Role]) -> Callable[..., None]:
    """Return a dependency that checks if the authenticated user has one of the allowed roles."""
    effective_roles = [*allowed_roles, Role.M4W]

    def _validate(username: PartnerUser) -> None:
        user_roles = _get_user_roles(username)
        if not any(role in effective_roles for role in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have the necessary permissions to access this resource.",
            )

    return _validate
