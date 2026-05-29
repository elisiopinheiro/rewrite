"""Lock schemas — acquire, release, list."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class _LockSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ClusterLockRead(_LockSchema):
    cluster_name: str
    locked: bool
    owner: str | None = None
    timeout_at: datetime
    created_at: datetime
    updated_at: datetime


class ClusterLockListResponse(_LockSchema):
    count: int
    items: list[ClusterLockRead]


class ClusterLockQuery(_LockSchema):
    cluster_name: str | None = None
    owner: str | None = None
    locked: bool | None = None
    token: str | None = None


class AcquireClusterLockRequest(_LockSchema):
    owner: str | None = None
    timeout_minutes: int = Field(default=360, ge=0, le=720)


class AcquireClusterLockResponse(_LockSchema):
    cluster_name: str
    message: str
    token: str
    timeout_at: datetime


class ReleaseClusterLockRequest(_LockSchema):
    token: str


class ReleaseClusterLockResponse(_LockSchema):
    cluster_name: str
    message: str
