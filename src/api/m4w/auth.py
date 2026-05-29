import os
import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

# Get basic username and password
BASIC_API_USERNAME = os.environ.get("BASIC_API_USERNAME", "ctw")
BASIC_API_PASSWORD = os.environ.get("BASIC_API_PASSWORD", "ctw")

BASIC_BACKFILL_USERNAME = os.environ.get("BASIC_BACKFILL_USERNAME", "ctw")
BASIC_BACKFILL_PASSWORD = os.environ.get("BASIC_BACKFILL_PASSWORD", "ctw")

security = HTTPBasic()


def validate_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, BASIC_API_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, BASIC_API_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def validate_backfill_credentials(
    credentials: HTTPBasicCredentials = Depends(security),
):
    correct_username = secrets.compare_digest(credentials.username, BASIC_BACKFILL_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, BASIC_BACKFILL_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password to perform backfill operations",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
