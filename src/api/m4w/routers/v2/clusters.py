"""Clusters v2 router methods"""

from typing import List, Union

from fastapi import APIRouter, Depends
from sqlalchemy.sql.elements import BinaryExpression

from api.m4w.auth import validate_credentials
from api.shared.enums import Environment
from api.shared.logger import logger
from api.shared.models.cluster_filters import ClusterFilters
from api.shared.models.clusters import (
    Cluster,
    ClusterList,
    OrderByClusterFields,
)
from api.shared.repository.cluster_repository import ClusterRepository

router = APIRouter(prefix="/v2/clusters", tags=["Clusters v2"])


@router.get(
    "",
    response_model=ClusterList,
)
def get_clusters_v2(
    filters: ClusterFilters = Depends(),
    locked: Union[bool, None] = None,
    order_by: Union[OrderByClusterFields, None] = "id",
    username: str = Depends(validate_credentials),
    cluster_repository: ClusterRepository = Depends(ClusterRepository),
) -> ClusterList:
    """
    \f Get cluster information with advanced filtering

    Args:
        filters (ClusterFilters, optional): Filters. Defaults to Depends().
        locked (Union[bool, None], optional): Locked. Defaults to None.
        order_by (Union[OrderByClusterFields, None], optional): Order by. Defaults to "id".
        username (str, optional): Username. Defaults to Depends(validate_credentials).
        cluster_repository (ClusterRepository, optional): Cluster repository. Defaults to Depends(ClusterRepository).

    Returns:
        ClusterList: Paginated cluster list

    Raises:
        HTTPValidationError: HTTP_422_UNPROCESSABLE_ENTITY if order_by value is not one of the allowed fields
    """
    logger.info("Received GET /v2/clusters request - filters: %s, locked: %s, order_by: %s", filters, locked, order_by)
    conditions: list[BinaryExpression] = filters.prepare_filters()

    clusters = cluster_repository.get_clusters_v2(
        condition_filters=conditions,
        locked=locked,
        order_by=order_by,
    )

    parsed_clusters = [cluster.build_response() for cluster in clusters]

    return ClusterList(count=len(parsed_clusters), clusters=parsed_clusters)


@router.get(
    "/releases",
    response_model=List[dict],
    tags=["Clusters v2"],
)
def get_releases_by_env(
    internal: bool = False,
    environment: Union[Environment, None] = None,
    username: str = Depends(validate_credentials),
    cluster_repository: ClusterRepository = Depends(ClusterRepository),
) -> List[dict]:
    """
    \f Get release information grouped by environment

    Args:
        internal (bool, optional): Internal clusters only. Defaults to False.
        environment (Union[Environment, None], optional): Environment filter. Defaults to None.
        username (str, optional): Username. Defaults to Depends(validate_credentials).
        cluster_repository (ClusterRepository, optional): Cluster repository. Defaults to Depends(ClusterRepository).

    Returns:
        List[dict]: Release information per environment
    """
    logger.info("Received GET /v2/clusters/releases request - internal: %s, environment: %s", internal, environment)
    args = locals()
    args.pop("username")
    args.pop("cluster_repository")
    parsed_args = {k: v for k, v in args.items() if v is not None}

    releases_by_env = cluster_repository.get_cluster_var_by_env(Cluster.release, **parsed_args)

    return [release._asdict() for release in releases_by_env]


@router.get(
    "/infra-revisions",
    response_model=List[dict],
    tags=["Clusters v2"],
)
def get_infra_revisions_by_env(
    internal: bool = False,
    environment: Union[Environment, None] = None,
    username: str = Depends(validate_credentials),
    cluster_repository: ClusterRepository = Depends(ClusterRepository),
) -> List[dict]:
    """
    \f Get infra revision information grouped by environment

    Args:
        internal (bool, optional): Internal clusters only. Defaults to False.
        environment (Union[Environment, None], optional): Environment filter. Defaults to None.
        username (str, optional): Username. Defaults to Depends(validate_credentials).
        cluster_repository (ClusterRepository, optional): Cluster repository. Defaults to Depends(ClusterRepository).

    Returns:
        List[dict]: Infra revision information per environment
    """
    logger.info(
        "Received GET /v2/clusters/infra-revisions request - internal: %s, environment: %s", internal, environment
    )
    args = locals()
    args.pop("username")
    args.pop("cluster_repository")
    parsed_args = {k: v for k, v in args.items() if v is not None}

    revisions_by_env = cluster_repository.get_cluster_var_by_env(Cluster.infra_revision, **parsed_args)

    return [revision._asdict() for revision in revisions_by_env]
