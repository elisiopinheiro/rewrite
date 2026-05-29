"""Release API routes."""

from fastapi import APIRouter, status

from app.deps import M4WUser, ReleaseSvc
from app.schemas.enums import Provider, ReleaseOrderBy
from app.schemas.releases import (
    ReleaseCreate,
    ReleaseDeleteResponse,
    ReleaseListQuery,
    ReleaseListResponse,
    ReleaseRead,
)

router = APIRouter(prefix="/releases", tags=["releases"])


@router.get("", response_model=ReleaseListResponse)
def list_releases(
    _user: M4WUser,
    service: ReleaseSvc,
    name: str | None = None,
    provider: Provider | None = None,
    order_by: ReleaseOrderBy = ReleaseOrderBy.ID,
) -> ReleaseListResponse:
    query = ReleaseListQuery(name=name, provider=provider, order_by=order_by)
    return service.list_releases(query)


@router.get("/{release_id}", response_model=ReleaseRead)
def get_release(
    release_id: int,
    _user: M4WUser,
    service: ReleaseSvc,
) -> ReleaseRead:
    return service.get_release(release_id)


@router.post("", response_model=ReleaseRead, status_code=status.HTTP_201_CREATED)
def create_release(
    _user: M4WUser,
    service: ReleaseSvc,
    payload: ReleaseCreate,
) -> ReleaseRead:
    return service.create_release(payload)


@router.delete("/{release_id}", response_model=ReleaseDeleteResponse)
def delete_release(
    release_id: int,
    _user: M4WUser,
    service: ReleaseSvc,
) -> ReleaseDeleteResponse:
    return service.delete_release(release_id)
