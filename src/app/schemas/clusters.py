"""Cluster schemas — create, read, patch, list, status."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import AzureSkuTier, ClusterOrderBy, ClusterStatus, Environment, Provider
from app.schemas.features import FeatureToggleCreate, FeatureToggleRead
from app.schemas.namespaces import ClientNamespaceRead, ClientNamespaceWrite
from app.schemas.node_pools import AdditionalNodePoolRead, AdditionalNodePoolWrite
from app.schemas.otlp_endpoints import ClientOTLPEndpointRead, ClientOTLPEndpointWrite
from app.schemas.storage_classes import StorageClassPayloadRead, StorageClassPayloadWrite
from app.schemas.user_features import UserFeatureRead, UserFeatureWrite
from app.schemas.webhooks import TeamsWebhookRead, TeamsWebhookWrite

# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


class ClusterCreateBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    subscription: str
    account_name: str | None = None
    release: str
    environment: Environment
    internal: bool
    repository: str
    multi_tenant: bool = False
    node_min_count: int
    node_max_count: int
    provider_region: str
    tshirt_size: str
    infra_revision: str
    kubernetes_version: str
    appd_id: str | None = None
    authorized_api_ip_ranges: list[str] | None = None
    dns_zone: str | None = None
    logging_retention_period: str | None = None
    tracing_retention_period: str | None = None
    pod_cidr: str | None = None
    service_cidr: str | None = None
    owner_group: str | None = None
    cmdb_app_id: str | None = None
    cmdb_appd_id: str | None = None
    network_cidr: str
    status: ClusterStatus | None = None
    uptime_period: str | None = None
    gateway_api_enabled: bool = False
    headlamp_enabled: bool = False
    domain_allowlist: list[str] = Field(default_factory=list)
    features: list[FeatureToggleCreate] = Field(default_factory=list)
    client_namespaces: list[ClientNamespaceWrite] = Field(default_factory=list)
    additional_node_pools: list[AdditionalNodePoolWrite] = Field(default_factory=list)
    teams_webhooks: TeamsWebhookWrite | None = None
    client_otlp_endpoints: list[ClientOTLPEndpointWrite] = Field(default_factory=list)


class AwsClusterCreate(ClusterCreateBase):
    provider: Literal["aws"]
    aws_vpc: str
    aws_vpc_endpoint_remote_account_ids: list[str] = Field(default_factory=list)
    aws_remote_account_ids: list[str] = Field(default_factory=list)
    # Optional, persisted as NULL when omitted (v3 normalized empty strings to NULL).
    vpc_endpoint_service_name: str | None = None
    vpc_endpoint_service_ingress_name: str | None = None
    cluster_oidc_issuer_url: str | None = None


class AzureClusterCreate(ClusterCreateBase):
    provider: Literal["azure"]
    azure_sku_tier: AzureSkuTier
    azure_subnet_name: str
    azure_vnet_name: str
    azure_vnet_resource_group: str
    dns_service_ip: str
    mi_agentpool_object_id: str | None = None
    mi_cluster_object_id: str | None = None
    storage_classes: StorageClassPayloadWrite | None = None


ClusterCreate = Annotated[AwsClusterCreate | AzureClusterCreate, Field(discriminator="provider")]


# ---------------------------------------------------------------------------
# Patch (JSON Merge Patch — all fields optional)
# ---------------------------------------------------------------------------


class ClusterPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    release: str | None = None
    node_min_count: int | None = None
    node_max_count: int | None = None
    tshirt_size: str | None = None
    infra_revision: str | None = None
    kubernetes_version: str | None = None
    owner_group: str | None = None
    cmdb_appd_id: str | None = None
    environment: Environment | None = None
    features: list[FeatureToggleCreate] | None = None
    user_features: list[UserFeatureWrite] | None = None
    status: ClusterStatus | None = None
    client_namespaces: list[ClientNamespaceWrite] | None = None
    logging_retention_period: str | None = None
    tracing_retention_period: str | None = None
    additional_node_pools: list[AdditionalNodePoolWrite] | None = None
    uptime_period: str | None = None
    multi_tenant: bool | None = None
    gateway_api_enabled: bool | None = None
    headlamp_enabled: bool | None = None
    domain_allowlist: list[str] | None = None
    teams_webhooks: TeamsWebhookWrite | None = None
    client_otlp_endpoints: list[ClientOTLPEndpointWrite] | None = None
    # AWS-specific
    aws_vpc_endpoint_remote_account_ids: list[str] | None = None
    aws_remote_account_ids: list[str] | None = None
    vpc_endpoint_service_name: str | None = None
    vpc_endpoint_service_ingress_name: str | None = None
    cluster_oidc_issuer_url: str | None = None
    # Azure-specific
    azure_sku_tier: AzureSkuTier | None = None
    mi_agentpool_object_id: str | None = None
    mi_cluster_object_id: str | None = None
    storage_classes: StorageClassPayloadWrite | None = None


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


class ClusterReadBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    name: str
    subscription: str
    account_name: str | None = None
    release: str
    environment: Environment
    internal: bool
    repository: str
    multi_tenant: bool
    node_min_count: int
    node_max_count: int
    provider_region: str
    tshirt_size: str
    infra_revision: str
    kubernetes_version: str
    appd_id: str | None = None
    authorized_api_ip_ranges: list[str] | None = None
    dns_zone: str | None = None
    logging_retention_period: str | None = None
    tracing_retention_period: str | None = None
    pod_cidr: str | None = None
    service_cidr: str | None = None
    owner_group: str | None = None
    cmdb_app_id: str | None = None
    cmdb_appd_id: str | None = None
    network_cidr: str
    status: ClusterStatus | None = None
    uptime_period: str | None = None
    gateway_api_enabled: bool
    headlamp_enabled: bool
    domain_allowlist: list[str]
    features: list[FeatureToggleRead]
    user_features: list[UserFeatureRead]
    client_namespaces: list[ClientNamespaceRead]
    additional_node_pools: list[AdditionalNodePoolRead]
    teams_webhooks: list[TeamsWebhookRead]
    client_otlp_endpoints: list[ClientOTLPEndpointRead]
    locked: bool
    is_in_downtime_window: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AwsClusterRead(ClusterReadBase):
    provider: Literal["aws"]
    # Nullable on the shared DB: v3_schema_fixes converts legacy empty strings to NULL.
    aws_vpc: str | None = None
    aws_vpc_endpoint_remote_account_ids: list[str]
    aws_remote_account_ids: list[str]
    vpc_endpoint_service_name: str | None = None
    vpc_endpoint_service_ingress_name: str | None = None
    cluster_oidc_issuer_url: str | None = None


class AzureClusterRead(ClusterReadBase):
    provider: Literal["azure"]
    # Nullable on the shared DB: these were added by later migrations / nulled by v3.
    azure_sku_tier: AzureSkuTier | None = None
    azure_subnet_name: str | None = None
    azure_vnet_name: str | None = None
    azure_vnet_resource_group: str | None = None
    dns_service_ip: str | None = None
    mi_agentpool_object_id: str | None = None
    mi_cluster_object_id: str | None = None
    storage_classes: StorageClassPayloadRead | None = None


ClusterRead = Annotated[AwsClusterRead | AzureClusterRead, Field(discriminator="provider")]


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


class ClusterListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    count: int
    items: list[ClusterRead]


class ClusterListQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    subscription: str | None = None
    account_name: str | None = None
    status: ClusterStatus | None = None
    provider: Provider | None = None
    release: str | None = None
    environment: Environment | None = None
    internal: bool | None = None
    multi_tenant: bool | None = None
    provider_region: str | None = None
    repository: str | None = None
    kubernetes_version: str | None = None
    owner_group: str | None = None
    cmdb_app_id: str | None = None
    cmdb_appd_id: str | None = None
    azure_sku_tier: AzureSkuTier | None = None
    locked: bool | None = None
    order_by: ClusterOrderBy = ClusterOrderBy.ID

    def repository_filters(self) -> dict[str, object]:
        return self.model_dump(exclude={"locked", "order_by"}, exclude_none=True)


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------


class ClusterStatusSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    name: str
    status: ClusterStatus | None = None


class ClusterStatusListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    count: int
    items: list[ClusterStatusSummary]


class BulkClusterStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ClusterStatus


class BulkClusterStatusUpdateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    count: int
    items: list[ClusterStatusSummary]


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


class ClusterDeleteResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str
