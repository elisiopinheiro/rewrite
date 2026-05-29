from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from contract.clusters.schemas.cluster_storage_classes import StorageClassContract
from pydantic import BaseModel, ConfigDict


class ProviderType(str, Enum):
    AWS = "aws"
    AZURE = "azure"


class BaseClusterResponseContractV1(BaseModel):
    """Base cluster fields shared across all providers"""

    model_config = ConfigDict(extra="forbid")

    id: int
    name: str
    subscription: str
    account_name: Optional[str] = None
    provider: ProviderType
    release: str
    environment: str
    internal: bool
    repository: str
    multi_tenant: bool
    node_min_count: int
    node_max_count: int
    provider_region: str
    tshirt_size: str
    infra_revision: str
    kubernetes_version: str
    network_cidr: str

    # Optional fields
    appd_id: Optional[str] = None
    authorized_api_ip_ranges: Optional[List[str]] = None
    dns_zone: Optional[str] = None
    logging_retention_period: Optional[str] = None
    tracing_retention_period: Optional[str] = None
    pod_cidr: Optional[str] = None
    service_cidr: Optional[str] = None
    owner_group: Optional[str] = None
    cmdb_app_id: Optional[str] = None
    cmdb_appd_id: Optional[str] = None
    status: Optional[str] = None
    uptime_period: Optional[str] = None
    gateway_api_enabled: Optional[bool] = None
    headlamp_enabled: Optional[bool] = None
    domain_allowlist: Optional[List[str]] = None
    features: Optional[List[Dict[str, Any]]] = None
    user_features: Optional[List[Dict[str, Any]]] = None
    client_namespaces: Optional[List[Dict[str, Any]]] = None
    client_otlp_endpoints: Optional[List[Dict[str, Any]]] = None
    additional_node_pools: Optional[List[Dict[str, Any]]] = None
    teams_webhooks: Optional[List[Dict[str, Any]]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    locked: bool = False
    is_in_downtime_window: bool = False


class AWSClusterResponseContractV1(BaseClusterResponseContractV1):
    """AWS-specific cluster contract"""

    model_config = ConfigDict(extra="forbid")

    provider: Literal[ProviderType.AWS] = ProviderType.AWS

    # Required AWS fields
    aws_vpc: str

    # Optional AWS fields
    aws_vpc_endpoint_remote_account_ids: Optional[List[str]] = None
    aws_remote_account_ids: Optional[List[str]] = None
    vpc_endpoint_service_name: Optional[str] = None
    vpc_endpoint_service_ingress_name: Optional[str] = None
    cluster_oidc_issuer_url: Optional[str] = None


class AzureClusterResponseContractV1(BaseClusterResponseContractV1):
    """Azure-specific cluster contract"""

    model_config = ConfigDict(extra="forbid")

    provider: Literal[ProviderType.AZURE] = ProviderType.AZURE

    # Required Azure fields
    azure_sku_tier: str
    azure_subnet_name: Optional[str] = None
    azure_vnet_name: Optional[str] = None
    azure_vnet_resource_group: Optional[str] = None
    dns_service_ip: Optional[str] = None
    mi_agentpool_object_id: Optional[str] = None
    mi_cluster_object_id: Optional[str] = None

    # Optional Azure fields
    storage_classes: Optional[StorageClassContract] = None


ClusterResponseContractV1 = Union[AWSClusterResponseContractV1, AzureClusterResponseContractV1]
