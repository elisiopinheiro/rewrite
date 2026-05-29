"""Cluster API routes."""

from fastapi import APIRouter, Query, status

from app.deps import ClusterSvc, M4WUser
from app.schemas.clusters import (
    BulkClusterStatusUpdateRequest,
    BulkClusterStatusUpdateResponse,
    ClusterCreate,
    ClusterDeleteResponse,
    ClusterListQuery,
    ClusterListResponse,
    ClusterPatch,
    ClusterRead,
    ClusterStatusListResponse,
)
from app.schemas.enums import AzureSkuTier, ClusterOrderBy, ClusterStatus, Environment, Provider

router = APIRouter(prefix="/clusters", tags=["clusters"])


# --- Static routes MUST come before dynamic {cluster_name} to avoid path collision ---


@router.get("/status", response_model=ClusterStatusListResponse)
def list_cluster_statuses(
    _user: M4WUser,
    service: ClusterSvc,
    name: str | None = None,
    subscription: str | None = None,
    account_name: str | None = None,
    cluster_status: ClusterStatus | None = Query(None, alias="status"),
    provider: Provider | None = None,
    release: str | None = None,
    environment: Environment | None = None,
    internal: bool | None = None,
    multi_tenant: bool | None = None,
    provider_region: str | None = None,
    repository: str | None = None,
    kubernetes_version: str | None = None,
    owner_group: str | None = None,
    cmdb_app_id: str | None = None,
    cmdb_appd_id: str | None = None,
    azure_sku_tier: AzureSkuTier | None = None,
    locked: bool | None = None,
    order_by: ClusterOrderBy = ClusterOrderBy.ID,
) -> ClusterStatusListResponse:
    query = ClusterListQuery(
        name=name,
        subscription=subscription,
        account_name=account_name,
        status=cluster_status,
        provider=provider,
        release=release,
        environment=environment,
        internal=internal,
        multi_tenant=multi_tenant,
        provider_region=provider_region,
        repository=repository,
        kubernetes_version=kubernetes_version,
        owner_group=owner_group,
        cmdb_app_id=cmdb_app_id,
        cmdb_appd_id=cmdb_appd_id,
        azure_sku_tier=azure_sku_tier,
        locked=locked,
        order_by=order_by,
    )
    return service.list_cluster_statuses(query)


@router.patch("/status", response_model=BulkClusterStatusUpdateResponse)
def update_cluster_statuses(
    _user: M4WUser,
    service: ClusterSvc,
    request: BulkClusterStatusUpdateRequest,
    name: str | None = None,
    subscription: str | None = None,
    account_name: str | None = None,
    cluster_status: ClusterStatus | None = Query(None, alias="status"),
    provider: Provider | None = None,
    release: str | None = None,
    environment: Environment | None = None,
    internal: bool | None = None,
    multi_tenant: bool | None = None,
    provider_region: str | None = None,
    repository: str | None = None,
    kubernetes_version: str | None = None,
    owner_group: str | None = None,
    cmdb_app_id: str | None = None,
    cmdb_appd_id: str | None = None,
    azure_sku_tier: AzureSkuTier | None = None,
    locked: bool | None = None,
    order_by: ClusterOrderBy = ClusterOrderBy.ID,
) -> BulkClusterStatusUpdateResponse:
    query = ClusterListQuery(
        name=name,
        subscription=subscription,
        account_name=account_name,
        status=cluster_status,
        provider=provider,
        release=release,
        environment=environment,
        internal=internal,
        multi_tenant=multi_tenant,
        provider_region=provider_region,
        repository=repository,
        kubernetes_version=kubernetes_version,
        owner_group=owner_group,
        cmdb_app_id=cmdb_app_id,
        cmdb_appd_id=cmdb_appd_id,
        azure_sku_tier=azure_sku_tier,
        locked=locked,
        order_by=order_by,
    )
    return service.update_cluster_statuses(query, request)


# --- Collection routes ---


@router.get("", response_model=ClusterListResponse)
def list_clusters(
    _user: M4WUser,
    service: ClusterSvc,
    name: str | None = None,
    subscription: str | None = None,
    account_name: str | None = None,
    cluster_status: ClusterStatus | None = Query(None, alias="status"),
    provider: Provider | None = None,
    release: str | None = None,
    environment: Environment | None = None,
    internal: bool | None = None,
    multi_tenant: bool | None = None,
    provider_region: str | None = None,
    repository: str | None = None,
    kubernetes_version: str | None = None,
    owner_group: str | None = None,
    cmdb_app_id: str | None = None,
    cmdb_appd_id: str | None = None,
    azure_sku_tier: AzureSkuTier | None = None,
    locked: bool | None = None,
    order_by: ClusterOrderBy = ClusterOrderBy.ID,
) -> ClusterListResponse:
    query = ClusterListQuery(
        name=name,
        subscription=subscription,
        account_name=account_name,
        status=cluster_status,
        provider=provider,
        release=release,
        environment=environment,
        internal=internal,
        multi_tenant=multi_tenant,
        provider_region=provider_region,
        repository=repository,
        kubernetes_version=kubernetes_version,
        owner_group=owner_group,
        cmdb_app_id=cmdb_app_id,
        cmdb_appd_id=cmdb_appd_id,
        azure_sku_tier=azure_sku_tier,
        locked=locked,
        order_by=order_by,
    )
    return service.list_clusters(query)


@router.post("", response_model=ClusterRead, status_code=status.HTTP_201_CREATED)
def create_cluster(
    _user: M4WUser,
    service: ClusterSvc,
    payload: ClusterCreate,
) -> ClusterRead:
    return service.create_cluster(payload)


# --- Resource routes (identified by cluster_name) ---


@router.get("/{cluster_name}", response_model=ClusterRead)
def get_cluster(
    cluster_name: str,
    _user: M4WUser,
    service: ClusterSvc,
) -> ClusterRead:
    return service.get_cluster_by_name(cluster_name)


@router.patch("/{cluster_name}", response_model=ClusterRead)
def update_cluster(
    cluster_name: str,
    _user: M4WUser,
    service: ClusterSvc,
    payload: ClusterPatch,
) -> ClusterRead:
    return service.update_cluster(cluster_name, payload)


@router.delete("/{cluster_name}", response_model=ClusterDeleteResponse)
def delete_cluster(
    cluster_name: str,
    _user: M4WUser,
    service: ClusterSvc,
) -> ClusterDeleteResponse:
    return service.delete_cluster(cluster_name)
