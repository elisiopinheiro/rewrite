"""Clusters v1 router methods"""

from typing import Annotated, List, Union

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from pydantic import Field as PydanticField
from sqlalchemy.exc import IntegrityError

from api.m4w.auth import validate_credentials
from api.shared.enums import AzureSkuTier, ClusterStatus, Environment, Provider
from api.shared.exceptions import InvalidProviderException, ReleaseNotFoundException
from api.shared.logger import logger
from api.shared.models.client_namespaces import ClientNamespace
from api.shared.models.client_otlp_endpoints import ClientOTLPEndpoint
from api.shared.models.clusters import (
    Cluster,
    ClusterAwsRequest,
    ClusterAwsResponse,
    ClusterAzureRequest,
    ClusterAzureResponse,
    ClusterUpdateData,
)
from api.shared.models.httperror import HTTPError
from api.shared.repository.cluster_repository import ClusterRepository

CLUSTERS_PREFIX = "/v1/clusters"
CLUSTER_NOT_FOUND = "Cluster not found"

ClusterRequest = Annotated[
    Union[ClusterAwsRequest, ClusterAzureRequest],
    PydanticField(discriminator="provider"),
]

ClusterResponse = Annotated[
    Union[ClusterAwsResponse, ClusterAzureResponse],
    PydanticField(discriminator="provider"),
]

router = APIRouter(prefix=CLUSTERS_PREFIX, tags=["Clusters v1"])


# This method will be deprecated after the column OWNER_GROUP (of Cluster) is changed to lowercase in the database # noqa: E501
# Use get_clusters_v2 instead
@router.get(
    "",
    response_model=List[ClusterResponse],
    responses={404: {"model": HTTPError}},
    deprecated=True,
)
def get_clusters(
    name: Union[str, None] = None,
    subscription: Union[str, None] = None,
    account_name: Union[str, None] = None,
    status: Union[ClusterStatus, None] = None,
    provider: Union[Provider, None] = None,
    release: Union[str, None] = None,
    environment: Union[Environment, None] = None,
    internal: Union[bool, None] = None,
    multi_tenant: Union[bool, None] = None,
    node_min_count: Union[int, None] = None,
    node_max_count: Union[int, None] = None,
    provider_region: Union[str, None] = None,
    tshirt_size: Union[str, None] = None,
    infra_revision: Union[str, None] = None,
    repository: Union[str, None] = None,
    kubernetes_version: Union[str, None] = None,
    owner_group: Union[str, None] = None,
    cmdb_app_id: Union[str, None] = None,
    cmdb_appd_id: Union[str, None] = None,
    azure_sku_tier: Union[AzureSkuTier, None] = None,
    locked: Union[bool, None] = None,
    order_by: Union[str, None] = "id",
    username: str = Depends(validate_credentials),
    cluster_repository: ClusterRepository = Depends(ClusterRepository),
) -> List[ClusterResponse]:
    """
    \f Get cluster information (deprecated, use v2)

    Args:
        name (Union[str, None], optional): Name. Defaults to None.
        subscription (Union[str, None], optional): Subscription. Defaults to None.
        account_name (Union[str, None], optional): Account name. Defaults to None.
        status (Union[ClusterStatus, None], optional): Status. Defaults to None.
        provider (Union[Provider, None], optional): Provider. Defaults to None.
        release (Union[str, None], optional): Release. Defaults to None.
        environment (Union[Environment, None], optional): Environment. Defaults to None.
        internal (Union[bool, None], optional): Internal. Defaults to None.
        multi_tenant (Union[bool, None], optional): Multi-tenant. Defaults to None.
        node_min_count (Union[int, None], optional): Minimum node count. Defaults to None.
        node_max_count (Union[int, None], optional): Maximum node count. Defaults to None.
        provider_region (Union[str, None], optional): Provider region. Defaults to None.
        tshirt_size (Union[str, None], optional): T-shirt size. Defaults to None.
        infra_revision (Union[str, None], optional): Infrastructure revision. Defaults to None.
        repository (Union[str, None], optional): Repository. Defaults to None.
        kubernetes_version (Union[str, None], optional): Kubernetes version. Defaults to None.
        owner_group (Union[str, None], optional): Owner group. Defaults to None.
        cmdb_app_id (Union[str, None], optional): CMDB APP ID. Defaults to None.
        cmdb_appd_id (Union[str, None], optional): CMDB APPD ID. Defaults to None.
        azure_sku_tier (Union[AzureSkuTier, None], optional): Azure SKU tier. Defaults to None.
        locked (Union[bool, None], optional): Locked. Defaults to None.
        order_by (Union[str, None], optional): Order by. Defaults to "id".
        username (str, optional): Username. Defaults to Depends(validate_credentials).
        cluster_repository (ClusterRepository, optional): Cluster repository. Defaults to Depends(ClusterRepository).

    Returns:
        List[Union[ClusterAwsResponse, ClusterAzureResponse]]: List of clusters
    """
    args = locals()
    args.pop("username")
    args.pop("order_by")
    args.pop("locked")
    args.pop("cluster_repository")
    parsed_args = {k: v for k, v in args.items() if v is not None}

    clusters: List[Cluster] = []

    clusters = cluster_repository.get_clusters_v1(locked=locked, filters=parsed_args, order_by=order_by)
    parsed_clusters = [cluster.build_response() for cluster in clusters]

    if not parsed_clusters:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="No clusters found",
        )

    return parsed_clusters


@router.post(
    "",
    responses={409: {"model": HTTPError}, 422: {"model": HTTPError}},
    response_model=ClusterResponse,
)
def add_cluster(
    cluster_request: ClusterRequest,
    username: str = Depends(validate_credentials),
    cluster_repository: ClusterRepository = Depends(ClusterRepository),
) -> ClusterResponse:
    """
    \f Add a new cluster

    Args:
        cluster_request (Union[ClusterAwsRequest, ClusterAzureRequest]): Cluster request payload
        username (str, optional): Username. Defaults to Depends(validate_credentials).
        cluster_repository (ClusterRepository, optional): Cluster repository. Defaults to Depends(ClusterRepository).

    Raises:
        HTTPException: HTTP_409_CONFLICT if cluster already exists
        HTTPException: HTTP_422_UNPROCESSABLE_CONTENT if request data is invalid

    Returns:
        Union[ClusterAwsResponse, ClusterAzureResponse]: Created cluster
    """
    logger.info("Received POST /v1/clusters request - body: %s", cluster_request.model_dump())
    try:
        return cluster_repository.add_cluster(cluster_request=cluster_request)
    except IntegrityError as e:
        logger.exception("")
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Cluster already exists",
        ) from e
    except ValueError as e:
        logger.exception("")
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(e),
        ) from e


# {id} endpoints on a separate router for include_router ordering control
router_with_id = APIRouter(prefix=CLUSTERS_PREFIX, tags=["Clusters v1"])


@router_with_id.get(
    "/{id}",
    response_model=ClusterResponse,
    responses={404: {"model": HTTPError}},
)
def get_cluster(
    id: int,
    username: str = Depends(validate_credentials),
    cluster_repository: ClusterRepository = Depends(ClusterRepository),
) -> ClusterResponse:
    """
    \f Get cluster by ID

    Args:
        id (int): Cluster ID
        username (str, optional): Username. Defaults to Depends(validate_credentials).
        cluster_repository (ClusterRepository, optional): Cluster repository. Defaults to Depends(ClusterRepository).

    Raises:
        HTTPException: HTTP_404_NOT_FOUND if cluster does not exist

    Returns:
        Union[ClusterAwsResponse, ClusterAzureResponse]: Cluster data
    """
    logger.info("Received GET /v1/clusters/%s request", id)
    cluster = cluster_repository.get_cluster(id)
    if cluster is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=CLUSTER_NOT_FOUND,
        )
    return cluster.build_response()


@router_with_id.put(
    "/{id}",
    responses={404: {"model": HTTPError}, 422: {"model": HTTPError}},
    response_model=ClusterResponse,
)
def update_cluster(
    id: int,
    data: ClusterUpdateData,
    username: str = Depends(validate_credentials),
    cluster_repository: ClusterRepository = Depends(ClusterRepository),
) -> ClusterResponse:
    """
    \f Update cluster by ID

    Args:
        id (int): Cluster ID
        data (ClusterUpdateData): Update data
        username (str, optional): Username. Defaults to Depends(validate_credentials).
        cluster_repository (ClusterRepository, optional): Cluster repository. Defaults to Depends(ClusterRepository).

    Raises:
        HTTPException: HTTP_404_NOT_FOUND if cluster does not exist
        HTTPException: HTTP_422_UNPROCESSABLE_CONTENT if release not found, invalid value, or invalid provider

    Returns:
        Union[ClusterAwsResponse, ClusterAzureResponse]: Updated cluster
    """
    logger.info("Received PUT /v1/clusters/%s request - body: %s", id, data.model_dump())
    cluster = cluster_repository.get_cluster(id)
    if cluster is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=CLUSTER_NOT_FOUND,
        )

    try:
        parsed_data = data.build_for_provider(provider=cluster.provider, data=data)
        cluster = cluster_repository.update_cluster(cluster=cluster, update_data=parsed_data)
        return cluster
    except (ReleaseNotFoundException, ValueError, InvalidProviderException) as e:
        logger.exception("")
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(e),
        ) from e


@router_with_id.delete("/{id}", responses={404: {"model": HTTPError}}, response_model=None)
def delete_cluster(
    id: int,
    username: str = Depends(validate_credentials),
    cluster_repository: ClusterRepository = Depends(ClusterRepository),
) -> None:
    """
    \f Delete cluster by ID

    Args:
        id (int): Cluster ID
        username (str, optional): Username. Defaults to Depends(validate_credentials).
        cluster_repository (ClusterRepository, optional): Cluster repository. Defaults to Depends(ClusterRepository).

    Raises:
        HTTPException: HTTP_404_NOT_FOUND if cluster does not exist

    Returns:
        dict: Deletion confirmation
    """
    logger.info("Received DELETE /v1/clusters/%s request", id)
    cluster = cluster_repository.get_cluster(id)
    if cluster is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=CLUSTER_NOT_FOUND,
        )
    return cluster_repository.delete_cluster(cluster)


@router_with_id.get(
    "/{id}/client-otlp-endpoints",
    response_model=List[ClientOTLPEndpoint],
    responses={404: {"model": HTTPError}},
)
def get_client_otlp_endpoints(
    id: int,
    username: str = Depends(validate_credentials),
    cluster_repository: ClusterRepository = Depends(ClusterRepository),
) -> List[ClientOTLPEndpoint]:
    """
    \f Get cluster client OTLP endpoints

    Args:
        id (int): Cluster ID
        username (str, optional): Username. Defaults to Depends(validate_credentials).
        cluster_repository (ClusterRepository, optional): Cluster repository. Defaults to Depends(ClusterRepository).

    Raises:
        HTTPException: HTTP_404_NOT_FOUND if cluster does not exist

    Returns:
        List[ClientOTLPEndpoint]: Cluster's client OTLP endpoints
    """
    logger.info("Received GET /v1/clusters/%s/client-otlp-endpoints request", id)
    cluster = cluster_repository.get_cluster(id)
    if cluster is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=CLUSTER_NOT_FOUND,
        )

    return cluster.client_otlp_endpoints


@router.get(
    "/releases",
    response_model=List[dict],
    responses={404: {"model": HTTPError}},
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

    Raises:
        HTTPException: HTTP_404_NOT_FOUND if no releases found

    Returns:
        List[dict]: Release information per environment
    """
    logger.info("Received GET /v1/clusters/releases request - internal: %s, environment: %s", internal, environment)
    args = locals()
    args.pop("username")
    args.pop("cluster_repository")
    parsed_args = {k: v for k, v in args.items() if v is not None}

    releases_by_env = cluster_repository.get_cluster_var_by_env(Cluster.release, **parsed_args)

    result = [release._asdict() for release in releases_by_env]

    if not result:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="No releases found",
        )

    return result


@router.get(
    "/infra-revisions",
    response_model=List[dict],
    responses={404: {"model": HTTPError}},
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

    Raises:
        HTTPException: HTTP_404_NOT_FOUND if no revisions found

    Returns:
        List[dict]: Infra revision information per environment
    """
    logger.info(
        "Received GET /v1/clusters/infra-revisions request - internal: %s, environment: %s", internal, environment
    )
    args = locals()
    args.pop("username")
    args.pop("cluster_repository")
    parsed_args = {k: v for k, v in args.items() if v is not None}

    revisions_by_env = cluster_repository.get_cluster_var_by_env(Cluster.infra_revision, **parsed_args)

    result = [revision._asdict() for revision in revisions_by_env]

    if not result:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="No revisions found",
        )

    return result


@router.get(
    "/adgr",
    response_model=List[ClusterResponse],
)
def get_clusters_by_adgr_groups(
    adgr_group: str = Query(
        description="Single ADGR group (APPL_XXXXX/RN-XXXXX/RN_XXXXX)\
            or list (APPL_XXXXXX,RN-XXXXXX,RN_XXXXX,APPL_XXXXXX)",
    ),
    username: str = Depends(validate_credentials),
    cluster_repository: ClusterRepository = Depends(ClusterRepository),
) -> List[ClusterResponse]:
    """
    \f Get clusters by ADGR group(s)

    Args:
        adgr_group (str): Single ADGR group or comma-separated list of ADGR groups.
        username (str, optional): Username. Defaults to Depends(validate_credentials).
        cluster_repository (ClusterRepository, optional): Cluster repository. Defaults to Depends(ClusterRepository).

    Returns:
        List[Union[ClusterAwsResponse, ClusterAzureResponse]]: Clusters matching the ADGR groups
    """
    logger.info("Received GET /v1/clusters/adgr request - adgr_group: %s", adgr_group)
    groups = [group.strip() for group in adgr_group.split(",")]
    clusters = cluster_repository.get_clusters_with_adgr_groups(adgr_groups=groups)
    return clusters


@router_with_id.get(
    "/{id}/client-namespaces",
    response_model=List[ClientNamespace],
    responses={404: {"model": HTTPError}},
)
def get_client_namespaces(
    id: int,
    username: str = Depends(validate_credentials),
    cluster_repository: ClusterRepository = Depends(ClusterRepository),
) -> List[ClientNamespace]:
    """
    \f Get client namespaces for a cluster

    Args:
        id (int): Cluster ID
        username (str, optional): Username. Defaults to Depends(validate_credentials).
        cluster_repository (ClusterRepository, optional): Cluster repository. Defaults to Depends(ClusterRepository).

    Raises:
        HTTPException: HTTP_404_NOT_FOUND if cluster does not exist

    Returns:
        List[ClientNamespace]: Cluster's client namespaces
    """
    logger.info("Received GET /v1/clusters/%s/client-namespaces request", id)
    cluster = cluster_repository.get_cluster(id)
    if cluster is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Cluster not found",
        )

    namespaces = cluster.client_namespaces
    return namespaces
