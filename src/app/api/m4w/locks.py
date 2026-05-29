"""Lock API routes."""

from fastapi import APIRouter, status

from app.deps import LockSvc, M4WUser
from app.schemas.locks import (
    AcquireClusterLockRequest,
    AcquireClusterLockResponse,
    ClusterLockListResponse,
    ClusterLockQuery,
    ReleaseClusterLockRequest,
    ReleaseClusterLockResponse,
)

router = APIRouter(tags=["locks"])


@router.get("/locks", response_model=ClusterLockListResponse, status_code=status.HTTP_200_OK)
def list_locks(
    _user: M4WUser,
    service: LockSvc,
    cluster_name: str | None = None,
    owner: str | None = None,
    locked: bool | None = None,
    token: str | None = None,
) -> ClusterLockListResponse:
    query = ClusterLockQuery(cluster_name=cluster_name, owner=owner, locked=locked, token=token)
    return service.list_locks(query)


@router.post(
    "/clusters/{cluster_name}/lock",
    response_model=AcquireClusterLockResponse,
    status_code=status.HTTP_201_CREATED,
)
def acquire_lock(
    cluster_name: str,
    user: M4WUser,
    service: LockSvc,
    request: AcquireClusterLockRequest,
) -> AcquireClusterLockResponse:
    return service.acquire_lock(cluster_name, request, username=user)


@router.delete(
    "/clusters/{cluster_name}/lock",
    response_model=ReleaseClusterLockResponse,
    status_code=status.HTTP_200_OK,
)
def release_lock(
    cluster_name: str,
    _user: M4WUser,
    service: LockSvc,
    request: ReleaseClusterLockRequest,
) -> ReleaseClusterLockResponse:
    return service.release_lock(cluster_name, request)
