"""Operations router methods"""

from datetime import datetime
from typing import List, Union

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status

from api.m4w.auth import validate_credentials
from api.shared.logger import logger
from api.shared.models.httperror import HTTPError
from api.shared.models.operation import Operation, OperationCreate
from api.shared.repository.cluster_repository import ClusterRepository
from api.shared.repository.operation_repository import OperationRepository

router_cluster_ops = APIRouter(prefix="/v1")
router = APIRouter(prefix="/v1")


@router_cluster_ops.get(
    "/clusters/{id}/operations",
    response_model=List[Operation],
    responses={404: {"model": HTTPError}},
    tags=["Clusters v1", "Operations v1"],
)
def get_cluster_operations(
    id: int,
    username: str = Depends(validate_credentials),
    cluster_repository: ClusterRepository = Depends(ClusterRepository),
    operation_repository: OperationRepository = Depends(OperationRepository),
) -> List[Operation]:
    """
    \f Get operations for a specific cluster

    Args:
        id (int): Cluster ID
        username (str, optional): Username. Defaults to Depends(validate_credentials).
        cluster_repository (ClusterRepository, optional): Cluster repository.
        Defaults to Depends(ClusterRepository).
        operation_repository (OperationRepository, optional): Operation repository.
        Defaults to Depends(OperationRepository).

    Raises:
        HTTPException: HTTP_404_NOT_FOUND if cluster does not exist

    Returns:
        List[Operation]: Cluster's operations
    """
    logger.info("Received GET /v1/clusters/%s/operations request", id)
    cluster = cluster_repository.get_cluster(id)
    if cluster is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Cluster not found",
        )

    operations = operation_repository.get_cluster_operations(id)
    return operations


@router_cluster_ops.post(
    "/clusters/{id}/operations",
    responses={404: {"model": HTTPError}},
    tags=["Clusters v1", "Operations v1"],
    response_model=Operation,
)
def add_operation(
    id: int,
    operation: OperationCreate,
    username: str = Depends(validate_credentials),
    cluster_repository: ClusterRepository = Depends(ClusterRepository),
    operation_repository: OperationRepository = Depends(OperationRepository),
) -> Operation:
    """
    \f Create an operation for a cluster

    Args:
        id (int): Cluster ID
        operation (OperationCreate): Operation data
        username (str, optional): Username. Defaults to Depends(validate_credentials).
        cluster_repository (ClusterRepository, optional): Cluster repository. Defaults to Depends(ClusterRepository).
        operation_repository (OperationRepository, optional): Operation repository.
        Defaults to Depends(OperationRepository).

    Raises:
        HTTPException: HTTP_404_NOT_FOUND if cluster does not exist

    Returns:
        Operation: Created operation
    """
    logger.info("Received POST /v1/clusters/%s/operations request - body: %s", id, operation.model_dump())
    cluster = cluster_repository.get_cluster(id)
    if cluster is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Cluster not found",
        )

    operation = Operation.model_validate(operation)
    operation.timestamp = datetime.now()
    operation.cluster_id = cluster.id
    # this is a test
    return operation_repository.save_operation(operation)


@router.get(
    "/operations",
    response_model=List[Operation],
    responses={404: {"model": HTTPError}},
    tags=["Operations v1"],
)
def get_operations(
    type: Union[str, None] = None,
    status: Union[str, None] = None,
    cicd_url: Union[str, None] = None,
    cluster_repository: Union[str, None] = None,
    username: str = Depends(validate_credentials),
    operation_repository: OperationRepository = Depends(OperationRepository),
) -> List[Operation]:
    """
    \f Get operations with optional filters

    Args:
        type (Union[str, None], optional): Operation type. Defaults to None.
        status (Union[str, None], optional): Operation status. Defaults to None.
        cicd_url (Union[str, None], optional): CICD URL. Defaults to None.
        cluster_repository (Union[str, None], optional): Cluster repository. Defaults to None.
        username (str, optional): Username. Defaults to Depends(validate_credentials).
        operation_repository (OperationRepository, optional): Operation repository.
        Defaults to Depends(OperationRepository).

    Raises:
        HTTPException: HTTP_404_NOT_FOUND if no operations match the filters

    Returns:
        List[Operation]: List of operations
    """
    args = locals()
    args.pop("username")
    args.pop("operation_repository")
    parsed_args = {k: v for k, v in args.items() if v}
    logger.info("Received GET /v1/operations request - filters: %s", parsed_args)
    operations = operation_repository.get_operations(**parsed_args)

    if not operations:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Operation not found",
        )

    return operations
