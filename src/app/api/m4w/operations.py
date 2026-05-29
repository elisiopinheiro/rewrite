"""Operation API routes."""

from fastapi import APIRouter
from fastapi import status as http_status

from app.core.types import HttpsUrl
from app.deps import M4WUser, OperationSvc
from app.schemas.operations import (
    OperationCreate,
    OperationListQuery,
    OperationListResponse,
    OperationRead,
)

router = APIRouter(tags=["operations"])


@router.get("/operations", response_model=OperationListResponse)
def list_operations(
    _user: M4WUser,
    service: OperationSvc,
    operation_type: str | None = None,
    status: str | None = None,
    cicd_url: HttpsUrl | None = None,
    cluster_repository: str | None = None,
) -> OperationListResponse:
    query = OperationListQuery(
        operation_type=operation_type,
        status=status,
        cicd_url=cicd_url,
        cluster_repository=cluster_repository,
    )
    return service.list_operations(query)


@router.get("/clusters/{cluster_name}/operations", response_model=OperationListResponse)
def list_cluster_operations(
    cluster_name: str,
    _user: M4WUser,
    service: OperationSvc,
) -> OperationListResponse:
    return service.list_cluster_operations(cluster_name)


@router.post(
    "/clusters/{cluster_name}/operations",
    response_model=OperationRead,
    status_code=http_status.HTTP_201_CREATED,
)
def create_operation(
    cluster_name: str,
    _user: M4WUser,
    service: OperationSvc,
    request: OperationCreate,
) -> OperationRead:
    return service.create_operation(cluster_name, request)
