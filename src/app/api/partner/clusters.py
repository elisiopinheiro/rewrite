"""Partner API routes — limited read-only endpoints for external consumers."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.partner.schemas import (
    ScpClusterListResponse,
    ScpClusterRead,
    SolarClusterListResponse,
    SolarClusterRead,
)
from app.core.security import Role, require_roles
from app.deps import ClusterSvc, PartnerUser
from app.schemas.clusters import AzureClusterRead, ClusterListQuery
from app.schemas.enums import Provider

router = APIRouter(prefix="/partners", tags=["partners"])

ClusterFilters = Annotated[ClusterListQuery, Query()]


@router.get(
    "/scp/clusters",
    response_model=ScpClusterListResponse,
    dependencies=[Depends(require_roles([Role.SCP, Role.CF]))],
)
def list_scp_clusters(
    _user: PartnerUser,
    service: ClusterSvc,
    query: ClusterFilters,
) -> ScpClusterListResponse:
    """List Azure clusters for SCP/CF partners. provider and internal are forced server-side."""
    scoped_query = query.model_copy(update={"provider": Provider.AZURE, "internal": False})
    response = service.list_clusters(scoped_query)
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
        if isinstance(cluster, AzureClusterRead)
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
    query: ClusterFilters,
) -> SolarClusterListResponse:
    """List all clusters for the SOLAR partner."""
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
