"""Partner-facing schemas — limited field sets for external consumers."""

from pydantic import BaseModel, ConfigDict


class ScpClusterRead(BaseModel):
    """Cluster subset exposed to SCP/CF partners (Azure only, non-internal)."""

    model_config = ConfigDict(extra="forbid")

    id: int
    name: str
    subscription: str
    provider_region: str
    azure_vnet_name: str
    azure_vnet_resource_group: str
    network_cidr: str
    cmdb_app_id: str | None = None
    cmdb_appd_id: str | None = None


class ScpClusterListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    count: int
    items: list[ScpClusterRead]


class SolarClusterRead(BaseModel):
    """Cluster subset exposed to SOLAR partner."""

    model_config = ConfigDict(extra="forbid")

    id: int
    name: str
    subscription: str
    account_name: str | None = None
    provider: str
    multi_tenant: bool
    provider_region: str
    cmdb_app_id: str | None = None
    cmdb_appd_id: str | None = None


class SolarClusterListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    count: int
    items: list[SolarClusterRead]
