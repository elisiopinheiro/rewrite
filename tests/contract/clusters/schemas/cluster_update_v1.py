from enum import Enum
from typing import Any, Dict, List, Optional, Union

from contract.clusters.schemas.cluster_storage_classes import StorageClassContract
from pydantic import BaseModel, ConfigDict


class Environment(str, Enum):
    TEST = "test"
    DEV = "development"
    INT = "integration"
    PRE_PROD = "pre-production"
    PROD = "production"


class ClusterStatus(str, Enum):
    RUNNING = "running"
    FREEZE = "freeze"


class AzureSkuTier(str, Enum):
    FREE = "Free"
    STANDARD = "Standard"


class BaseClusterUpdateRequestContractV1(BaseModel):
    """Base schema for cluster update requests"""

    model_config = ConfigDict(extra="forbid")

    release: Optional[str] = None
    node_min_count: Optional[int] = None
    node_max_count: Optional[int] = None
    tshirt_size: Optional[str] = None
    infra_revision: Optional[str] = None
    kubernetes_version: Optional[str] = None
    owner_group: Optional[str] = None
    cmdb_appd_id: Optional[str] = None
    environment: Optional[Environment] = None
    features: Optional[List[Dict[str, Any]]] = None
    user_features: Optional[List[Dict[str, Any]]] = None
    status: Optional[ClusterStatus] = None
    client_namespaces: Optional[List[Dict[str, Any]]] = None
    logging_retention_period: Optional[str] = None
    tracing_retention_period: Optional[str] = None
    additional_node_pools: Optional[List[Dict[str, Any]]] = None
    kubedownscaler_downscale_period: Optional[str] = None
    kubedownscaler_upscale_period: Optional[str] = None
    uptime_period: Optional[str] = None
    multi_tenant: Optional[bool] = None
    gateway_api_enabled: Optional[bool] = None
    headlamp_enabled: Optional[bool] = None
    domain_allowlist: Optional[List[str]] = None
    teams_webhooks: Optional[Dict[str, Dict[str, List[str]]]] = None
    client_otlp_endpoints: Optional[List[Dict[str, Any]]] = None


class ClusterAwsUpdateRequestContractV1(BaseClusterUpdateRequestContractV1):
    """Schema for AWS cluster update requests"""

    model_config = ConfigDict(extra="forbid")

    aws_vpc_endpoint_remote_account_ids: Optional[List[str]] = None
    aws_remote_account_ids: Optional[List[str]] = None
    vpc_endpoint_service_name: Optional[str] = None
    vpc_endpoint_service_ingress_name: Optional[str] = None
    cluster_oidc_issuer_url: Optional[str] = None


class ClusterAzureUpdateRequestContractV1(BaseClusterUpdateRequestContractV1):
    """Schema for Azure cluster update requests"""

    model_config = ConfigDict(extra="forbid")

    azure_sku_tier: Optional[AzureSkuTier] = None
    mi_agentpool_object_id: Optional[str] = None
    mi_cluster_object_id: Optional[str] = None
    storage_classes: Optional[StorageClassContract] = None


ClusterUpdateRequestContractV1 = Union[ClusterAwsUpdateRequestContractV1, ClusterAzureUpdateRequestContractV1]
