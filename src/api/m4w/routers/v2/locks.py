"""Locks v2 router methods"""

from typing import List, Union

from fastapi import APIRouter, Depends

from api.m4w.auth import validate_credentials
from api.shared.logger import logger
from api.shared.models.clusters import ClusterLock
from api.shared.repository.cluster_repository import ClusterRepository

router = APIRouter(tags=["Locks v2"])


@router.get(
    "/v2/locks",
    response_model=List[ClusterLock],
)
def get_clusters_locks_v2(
    cluster_name: Union[str, None] = None,
    owner: Union[str, None] = None,
    locked: Union[bool, None] = None,
    token: Union[str, None] = None,
    username: str = Depends(validate_credentials),
    cluster_repository: ClusterRepository = Depends(ClusterRepository),
) -> List[ClusterLock]:
    """
    \f Method to get cluster locks

    Args:
        cluster_name (Union[str, None], optional): Cluster name. Defaults to None.
        owner (Union[str, None], optional): Owner. Defaults to None.
        locked (Union[bool, None], optional): Locked. Defaults to None.
        token (Union[str, None], optional): Token. Defaults to None.
        username (str, optional): Username. Defaults to Depends(validate_credentials).

    Returns:
        locks: Clusters locks
    """
    logger.info("Received GET /v2/locks request - cluster_name: %s, locked: %s", cluster_name, locked)
    args = locals()
    args.pop("username")
    args.pop("cluster_repository")
    parsed_args = {k: v for k, v in args.items() if v is not None}

    locks = cluster_repository.get_cluster_locks(**parsed_args)

    return locks
