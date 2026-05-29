import os
import secrets
from enum import Enum
from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

# Get basic username and password
BASIC_M4W_API_USERNAME = os.environ.get("BASIC_M4W_API_USERNAME", "ctw")
BASIC_M4W_API_PASSWORD = os.environ.get("BASIC_M4W_API_PASSWORD", "ctw")

BASIC_CLOUD_API_USERNAME = os.environ.get("BASIC_CLOUD_API_USERNAME", "cf")
BASIC_CLOUD_API_PASSWORD = os.environ.get("BASIC_CLOUD_API_PASSWORD", "cf")

BASIC_SCP_API_USERNAME = os.environ.get("BASIC_SCP_API_USERNAME", "scp")
BASIC_SCP_API_PASSWORD = os.environ.get("BASIC_SCP_API_PASSWORD", "scp")

BASIC_SOLAR_API_USERNAME = os.environ.get("BASIC_SOLAR_API_USERNAME", "solar")
BASIC_SOLAR_API_PASSWORD = os.environ.get("BASIC_SOLAR_API_PASSWORD", "solar")


security = HTTPBasic()


def _authenticate_credentials(credentials: HTTPBasicCredentials, username: str, password: str) -> bool:
    correct_username = secrets.compare_digest(credentials.username, username)
    correct_password = secrets.compare_digest(credentials.password, password)
    return correct_username and correct_password


def validate_credentials(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    authenticated = any(
        _authenticate_credentials(credentials, username, password)
        for username, password in [
            (BASIC_M4W_API_USERNAME, BASIC_M4W_API_PASSWORD),
            (BASIC_CLOUD_API_USERNAME, BASIC_CLOUD_API_PASSWORD),
            (BASIC_SCP_API_USERNAME, BASIC_SCP_API_PASSWORD),
            (BASIC_SOLAR_API_USERNAME, BASIC_SOLAR_API_PASSWORD),
        ]
    )

    if not authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


# Authorization
class Role(str, Enum):
    M4W = "4Wheels Managed"
    CF = "Cloud Foundation"
    SCP = "Standard Cloud Platform"
    SOLAR = "Solution Landscape and Anomaly Reporter"


USERS_ROLES_MAPPING = {
    BASIC_M4W_API_USERNAME: [Role.M4W],
    BASIC_CLOUD_API_USERNAME: [Role.CF],
    BASIC_SCP_API_USERNAME: [Role.SCP],
    BASIC_SOLAR_API_USERNAME: [Role.SOLAR],
}


def validate_user_role(allowed_roles: list[Role]) -> Callable:
    """
    Validates that the authenticated user has at least one of the required roles.
    M4W role is automatically added for all endpoints.
    """

    def validate(username: str = Depends(validate_credentials)) -> None:
        allowed_roles.append(Role.M4W)
        user_roles = USERS_ROLES_MAPPING.get(username, [])

        if not any(role in set(allowed_roles) for role in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have the necessary permissions to access this resource.",
            )

    return validate
