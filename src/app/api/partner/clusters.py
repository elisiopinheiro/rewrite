"""Partner API routes — limited read-only endpoints for external consumers."""

from fastapi import APIRouter, Depends, Query

from app.api.partner.schemas import (
    ScpClusterListResponse,
    ScpClusterRead,
    SolarClusterListResponse,
    SolarClusterRead,
)
from app.core.security import Role, require_roles
from app.deps import ClusterSvc, PartnerUser
from app.schemas.clusters import ClusterListQuery
from app.schemas.enums import AzureSkuTier, ClusterOrderBy, ClusterStatus, Environment, Provider

router = APIRouter(prefix="/partners", tags=["partners"])


@router.get(
    "/scp/clusters",
    response_model=ScpClusterListResponse,
    dependencies=[Depends(require_roles([Role.SCP, Role.CF]))],
)
def list_scp_clusters(
    _user: PartnerUser,
    service: ClusterSvc,
    name: str | None = None,
    subscription: str | None = None,
    account_name: str | None = None,
    cluster_status: ClusterStatus | None = Query(None, alias="status"),
    release: str | None = None,
    environment: Environment | None = None,
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
) -> ScpClusterListResponse:
    """List Azure clusters for SCP/CF partners. Forces provider=azure, internal=False."""
    query = ClusterListQuery(
        name=name,
        subscription=subscription,
        account_name=account_name,
        status=cluster_status,
        provider=Provider.AZURE,
        release=release,
        environment=environment,
        internal=False,
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
    response = service.list_clusters(query)
    items = [
        ScpClusterRead(
            id=cluster.id,
            name=cluster.name,
            subscription=cluster.subscription,
            provider_region=cluster.provider_region,
            azure_vnet_name=cluster.azure_vnet_name,
            azure_vnet_resource_group=cluster.azure_vnet_resource_group,
            network_cidr=cluster.network_cidr,
            cmdb_app_id=cluster.cmdb_app_id,
            cmdb_appd_id=cluster.cmdb_appd_id,
        )
        for cluster in response.items
        if cluster.provider == Provider.AZURE
    ]
    return ScpClusterListResponse(count=len(items), items=items)


@router.get(
    "/solar/clusters",
    response_model=SolarClusterListResponse,
    dependencies=[Depends(require_roles([Role.SOLAR]))],
)
def list_solar_clusters(
    _user: PartnerUser,
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
) -> SolarClusterListResponse:
    """List all clusters for SOLAR partner."""
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
    response = service.list_clusters(query)
    items = [
        SolarClusterRead(
            id=cluster.id,
            name=cluster.name,
            subscription=cluster.subscription,
            account_name=cluster.account_name,
            provider=cluster.provider,
            multi_tenant=cluster.multi_tenant,
            provider_region=cluster.provider_region,
            cmdb_app_id=cluster.cmdb_app_id,
            cmdb_appd_id=cluster.cmdb_appd_id,
        )
        for cluster in response.items
    ]
    return SolarClusterListResponse(count=len(items), items=items)
