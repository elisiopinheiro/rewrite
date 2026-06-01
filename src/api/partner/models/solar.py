"""Models for SOLAR endpoints"""

from typing import List, Optional

from pydantic import BaseModel
from sqlmodel import SQLModel

from api.shared.models.cluster_filters import FilterMixin
from api.shared.models.clusters import Provider


class SOLARClusterResponse(SQLModel):
    name: str  # Should be unique
    subscription: str
    account_name: str
    provider: str
    multi_tenant: bool
    provider_region: str
    cmdb_app_id: Optional[str] = None
    cmdb_appd_id: Optional[str] = None


class SOLARClusterList(BaseModel):
    count: int
    clusters: Optional[List[SOLARClusterResponse]] = None


# Filters
class SOLARClusterFilters(FilterMixin, BaseModel):
    name: Optional[str] = None
    subscription: Optional[str] = None
    account_name: Optional[str] = None
    provider: Optional[Provider] = None
    multi_tenant: Optional[bool] = None
    provider_region: Optional[str] = None
    cmdb_app_id: Optional[str] = None
    cmdb_appd_id: Optional[str] = None
