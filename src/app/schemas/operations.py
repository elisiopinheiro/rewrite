"""Operation schemas — create, read, list."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.core.types import HttpsUrl


class OperationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation_type: str
    status: str
    cicd_url: HttpsUrl
    timestamp: datetime | None = None
    cluster_repository: str | None = None


class OperationRead(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    cluster_id: int | None = None
    operation_type: str
    status: str
    cicd_url: HttpsUrl
    timestamp: datetime | None = None
    cluster_repository: str | None = None


class OperationListQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation_type: str | None = None
    status: str | None = None
    cicd_url: HttpsUrl | None = None
    cluster_repository: str | None = None


class OperationListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    count: int
    items: list[OperationRead]
