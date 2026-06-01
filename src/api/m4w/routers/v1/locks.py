"""Locks router methods"""

from typing import List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.exc import OperationalError

from api.m4w.auth import validate_credentials
from api.shared.config import DEFAULT_LOCK_TIMEOUT_MINUTES
from api.shared.exceptions import (
    ClusterNotLockedException,
    LockException,
)
from api.shared.logger import logger
from api.shared.models.clusters import ClusterLockRead, LockResponse, UnlockResponse
from api.shared.models.httperror import HTTPError
from api.shared.repository.cluster_repository import ClusterRepository

router_lock_unlock = APIRouter()
router = APIRouter()


@router_lock_unlock.put(
    "/v1/clusters/{name}/lock",
    response_model=LockResponse,
    responses={404: {"model": HTTPError}, 423: {"model": HTTPError}},
    tags=["Locks v1"],
)
def lock_cluster(
    name: str,
    owner: Optional[str] = Query(default=None),
    lock_owner: Optional[str] = Query(default=None, alias="lock_owner", include_in_schema=False),
    timeout: int = Query(default=DEFAULT_LOCK_TIMEOUT_MINUTES, ge=0, le=720),
    username: str = Depends(validate_credentials),
    cluster_repository: ClusterRepository = Depends(ClusterRepository),
) -> LockResponse:
    """
    \f Method to lock cluster

    Args:
        name (str): Name
        owner (str, optional): Lock owner. Defaults to None.
        lock_owner (str, optional): Lock owner (deprecated alias). Defaults to None.
        timeout (int, optional): Timeout. Defaults to Query(default=DEFAULT_LOCK_TIMEOUT_MINUTES, ge=0, le=720).
        username (str, optional): Username. Defaults to Depends(validate_credentials).

    Raises:
        HTTPException: HTTP_404_NOT_FOUND if cluster does not exist
        HTTPException: HTTP_423_LOCKED if cluster is already locked or lock cannot be acquired

    Returns:
        LockResponse: Lock confirmation with token
    """
    owner = owner or lock_owner
    cluster = cluster_repository.get_clusters_v1(filters={"name": name})  # returns maximum 1 because name is unique
    if not cluster:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Cluster not found",
        )
    cluster = cluster[0]
    logger.info(f"Requesting lock for cluster {name}")
    try:
        token = cluster_repository.lock_cluster(cluster, owner, timeout)
    except LockException as e:
        logger.exception("")
        raise HTTPException(
            status_code=http_status.HTTP_423_LOCKED,
            detail=str(e),
        ) from e
    except OperationalError as e:
        logger.exception("")
        raise HTTPException(
            status_code=http_status.HTTP_423_LOCKED,
            detail="Could not acquire cluster lock",
        ) from e

    return LockResponse(message="Cluster succesfully locked", token=str(token))


@router_lock_unlock.put(
    "/v1/clusters/{name}/unlock",
    response_model=UnlockResponse,
    responses={
        400: {"model": HTTPError},
        404: {"model": HTTPError},
        409: {"model": HTTPError},
        423: {"model": HTTPError},
        500: {"model": HTTPError},
    },
    tags=["Locks v1"],
)
def unlock_cluster(
    name: str,
    token: str,
    username: str = Depends(validate_credentials),
    cluster_repository: ClusterRepository = Depends(ClusterRepository),
) -> UnlockResponse:
    """
    \f Method to unlock cluster

    Args:
        name (str): Name
        token (str): Token
        username (str, optional): Username. Defaults to Depends(validate_credentials).

    Raises:
        HTTPException: HTTP_404_NOT_FOUND if cluster does not exist
        HTTPException: HTTP_409_CONFLICT if cluster is not locked
        HTTPException: HTTP_400_BAD_REQUEST if lock token does not match
        HTTPException: HTTP_423_LOCKED if cluster is being locked by another operation
        HTTPException: HTTP_500_INTERNAL_SERVER_ERROR on unexpected error

    Returns:
        UnlockResponse: Unlock confirmation
    """
    logger.info("Received PUT /v1/clusters/%s/unlock request", name)
    cluster = cluster_repository.get_clusters_v1(filters={"name": name})  # returns maximum 1 because name is unique
    if not cluster:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Cluster not found",
        )

    cluster = cluster[0]
    success = False
    try:
        success = cluster_repository.unlock_cluster(cluster, token)
    except ClusterNotLockedException as e:
        logger.exception("")
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e
    except LockException as e:
        logger.exception("")
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except OperationalError as e:
        logger.exception("")
        raise HTTPException(
            status_code=http_status.HTTP_423_LOCKED,
            detail="Cluster is being locked by another operation",
        ) from e

    if success:
        return UnlockResponse(message="Cluster successfully unlocked")
    else:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error",
        )


@router.get(
    "/v1/locks",
    response_model=List[ClusterLockRead],
    responses={404: {"model": HTTPError}},
    tags=["Locks v1"],
)
def get_clusters_locks(
    cluster_name: Union[str, None] = None,
    owner: Union[str, None] = None,
    locked: Union[bool, None] = None,
    token: Union[str, None] = None,
    username: str = Depends(validate_credentials),
    cluster_repository: ClusterRepository = Depends(ClusterRepository),
) -> List[ClusterLockRead]:
    """
    \f Method to get cluster locks

    Args:
        cluster_name (Union[str, None], optional): Cluster name. Defaults to None.
        owner (Union[str, None], optional): Owner. Defaults to None.
        locked (Union[bool, None], optional): Locked. Defaults to None.
        token (Union[str, None], optional): Token. Defaults to None.
        username (str, optional): Username. Defaults to Depends(validate_credentials).

    Raises:
        HTTPException: HTTP_404_NOT_FOUND if no locks found

    Returns:
        locks: Clusters locks
    """
    args = locals()
    args.pop("username")
    args.pop("cluster_repository")
    parsed_args = {k: v for k, v in args.items() if v is not None}
    logger.info("Received GET /v1/locks request - cluster_name: %s, locked: %s", cluster_name, locked)

    locks = cluster_repository.get_cluster_locks(**parsed_args)

    if not locks:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="No locks found",
        )

    return locks
