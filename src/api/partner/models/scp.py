"""Models for SCP and CLoud Foundation endpoints"""

from typing import List, Optional

from pydantic import BaseModel
from sqlmodel import SQLModel

from api.shared.models.cluster_filters import FilterMixin
from api.shared.models.clusters import Provider


class SCPClusterResponse(SQLModel):
    name: str  # Should be unique
    subscription: str
    provider_region: str
    azure_vnet_name: Optional[str] = None
    azure_vnet_resource_group: Optional[str] = None
    network_cidr: str
    cmdb_app_id: Optional[str] = None
    cmdb_appd_id: Optional[str] = None


class SCPClusterList(BaseModel):
    count: int
    clusters: Optional[List[SCPClusterResponse]] = None


# Filters
class SCPClusterFilters(FilterMixin, BaseModel):
    name: Optional[str] = None
    azure_vnet_name: Optional[str] = None
    azure_vnet_resource_group: Optional[str] = None
    cmdb_appd_id: Optional[str] = None
    provider_region: Optional[str] = None
    subscription: Optional[str] = None


class SCPClusterFiltersAzure(SCPClusterFilters):
    provider: Provider = "azure"
    internal: bool = False
