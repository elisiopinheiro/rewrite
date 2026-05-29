"""Status router methods"""

from typing import List, Union

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status

from api.m4w.auth import validate_credentials
from api.shared.enums import AzureSkuTier, ClusterStatus, Environment, Provider
from api.shared.logger import logger
from api.shared.models.clusters import (
    ClusterAwsResponse,
    ClusterAzureResponse,
    ClusterStatusResponse,
    OrderByClusterFields,
)
from api.shared.models.httperror import HTTPError
from api.shared.repository.cluster_repository import ClusterRepository

router = APIRouter(prefix="/v1/clusters")


@router.get(
    "/status",
    response_model=List[ClusterStatusResponse],
    tags=["Clusters v1", "Status"],
)
def get_status(
    name: Union[str, None] = None,
    subscription: Union[str, None] = None,
    account_name: Union[str, None] = None,
    status: Union[ClusterStatus, None] = None,
    provider: Union[Provider, None] = None,
    release: Union[str, None] = None,
    environment: Union[Environment, None] = None,
    internal: Union[bool, None] = None,
    provider_region: Union[str, None] = None,
    infra_revision: Union[str, None] = None,
    kubernetes_version: Union[str, None] = None,
    owner_group: Union[str, None] = None,
    cmdb_app_id: Union[str, None] = None,
    cmdb_appd_id: Union[str, None] = None,
    azure_sku_tier: Union[AzureSkuTier, None] = None,
    order_by: Union[OrderByClusterFields, None] = "id",
    username: str = Depends(validate_credentials),
    cluster_repository: ClusterRepository = Depends(ClusterRepository),
) -> List[ClusterStatusResponse]:
    """
    \f Get clusters status with optional filters

    Args:
        name (Union[str, None], optional): Name. Defaults to None.
        subscription (Union[str, None], optional): Subscription. Defaults to None.
        account_name (Union[str, None], optional): Account name. Defaults to None.
        status (Union[ClusterStatus, None], optional): Status. Defaults to None.
        provider (Union[Provider, None], optional): Provider. Defaults to None.
        release (Union[str, None], optional): Release. Defaults to None.
        environment (Union[Environment, None], optional): Environment. Defaults to None.
        internal (Union[bool, None], optional): Internal. Defaults to None.
        provider_region (Union[str, None], optional): Provider region. Defaults to None.
        infra_revision (Union[str, None], optional): Infra revision. Defaults to None.
        kubernetes_version (Union[str, None], optional): Kubernetes version. Defaults to None.
        owner_group (Union[str, None], optional): Owner group. Defaults to None.
        cmdb_app_id (Union[str, None], optional): CMDB APP ID. Defaults to None.
        cmdb_appd_id (Union[str, None], optional): CMDB APPD ID. Defaults to None.
        azure_sku_tier (Union[AzureSkuTier, None], optional): Azure SKU tier. Defaults to None.
        order_by (Union[OrderByClusterFields, None], optional): Order by. Defaults to "id".
        username (str, optional): Username. Defaults to Depends(validate_credentials).
        cluster_repository (ClusterRepository, optional): Cluster repository. Defaults to Depends(ClusterRepository).

    Returns:
        List[ClusterStatusResponse]: List of cluster names and statuses

    Raises:
        HTTPValidationError: HTTP_422_UNPROCESSABLE_ENTITY if order_by value is not one of the allowed fields
    """
    args = locals()
    args.pop("username")
    args.pop("order_by")
    args.pop("cluster_repository")
    parsed_args = {k: v for k, v in args.items() if v is not None}
    logger.info("Received GET /v1/clusters/status request - filters: %s, order_by: %s", parsed_args, order_by)
    clusters = cluster_repository.get_clusters_v1(filters=parsed_args, order_by=order_by)

    return [ClusterStatusResponse(cluster_name=cluster.name, status=cluster.status) for cluster in clusters]


@router.put(
    "/status",
    response_model=List[Union[ClusterAwsResponse, ClusterAzureResponse]],
    tags=["Clusters v1", "Status"],
)
def update_clusters_status(
    new_status: ClusterStatus,
    name: Union[str, None] = None,
    subscription: Union[str, None] = None,
    account_name: Union[str, None] = None,
    status: Union[ClusterStatus, None] = None,
    provider: Union[Provider, None] = None,
    release: Union[str, None] = None,
    environment: Union[Environment, None] = None,
    internal: Union[bool, None] = None,
    provider_region: Union[str, None] = None,
    infra_revision: Union[str, None] = None,
    kubernetes_version: Union[str, None] = None,
    owner_group: Union[str, None] = None,
    cmdb_app_id: Union[str, None] = None,
    cmdb_appd_id: Union[str, None] = None,
    azure_sku_tier: Union[AzureSkuTier, None] = None,
    gateway_api_enabled: Union[bool, None] = None,
    headlamp_enabled: Union[bool, None] = None,
    username: str = Depends(validate_credentials),
    cluster_repository: ClusterRepository = Depends(ClusterRepository),
) -> List[Union[ClusterAwsResponse, ClusterAzureResponse]]:
    """
    \f Update status for clusters matching filters

    Args:
        new_status (ClusterStatus): New status to set
        name (Union[str, None], optional): Name. Defaults to None.
        subscription (Union[str, None], optional): Subscription. Defaults to None.
        account_name (Union[str, None], optional): Account name. Defaults to None.
        status (Union[ClusterStatus, None], optional): Status. Defaults to None.
        provider (Union[Provider, None], optional): Provider. Defaults to None.
        release (Union[str, None], optional): Release. Defaults to None.
        environment (Union[Environment, None], optional): Environment. Defaults to None.
        internal (Union[bool, None], optional): Internal. Defaults to None.
        provider_region (Union[str, None], optional): Provider region. Defaults to None.
        infra_revision (Union[str, None], optional): Infra revision. Defaults to None.
        kubernetes_version (Union[str, None], optional): Kubernetes version. Defaults to None.
        owner_group (Union[str, None], optional): Owner group. Defaults to None.
        cmdb_app_id (Union[str, None], optional): CMDB APP ID. Defaults to None.
        cmdb_appd_id (Union[str, None], optional): CMDB APPD ID. Defaults to None.
        azure_sku_tier (Union[AzureSkuTier, None], optional): Azure SKU tier. Defaults to None.
        gateway_api_enabled (Union[bool, None], optional): Gateway API enabled. Defaults to None.
        headlamp_enabled (Union[bool, None], optional): Headlamp enabled. Defaults to None.
        username (str, optional): Username. Defaults to Depends(validate_credentials).
        cluster_repository (ClusterRepository, optional): Cluster repository. Defaults to Depends(ClusterRepository).

    Returns:
        List[Union[ClusterAwsResponse, ClusterAzureResponse]]: Updated clusters
    """
    args = locals()
    args.pop("username")
    args.pop("new_status")
    args.pop("cluster_repository")
    parsed_args = {k: v for k, v in args.items() if v is not None}
    logger.info("Received PUT /v1/clusters/status request - new_status: %s, filters: %s", new_status, parsed_args)
    clusters = cluster_repository.get_clusters_v1(filters=parsed_args)

    updated_clusters = []
    for cluster in clusters:
        updated_clusters.append(cluster_repository.update_cluster_status(cluster=cluster, new_status=new_status))

    return updated_clusters


@router.get(
    "/{id}/status",
    response_model=ClusterStatusResponse,
    responses={404: {"model": HTTPError}},
    tags=["Clusters v1", "Status"],
)
def get_status_by_id(
    id: int,
    username: str = Depends(validate_credentials),
    cluster_repository: ClusterRepository = Depends(ClusterRepository),
) -> ClusterStatusResponse:
    """
    \f Get status of a specific cluster by ID

    Args:
        id (int): Cluster ID
        username (str, optional): Username. Defaults to Depends(validate_credentials).
        cluster_repository (ClusterRepository, optional): Cluster repository. Defaults to Depends(ClusterRepository).

    Raises:
        HTTPException: HTTP_404_NOT_FOUND if cluster does not exist

    Returns:
        ClusterStatusResponse: Cluster name and status
    """
    logger.info("Received GET /v1/clusters/%s/status request", id)
    cluster = cluster_repository.get_cluster(id)

    if not cluster:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Cluster not found",
        )

    return ClusterStatusResponse(cluster_name=cluster.name, status=cluster.status)
