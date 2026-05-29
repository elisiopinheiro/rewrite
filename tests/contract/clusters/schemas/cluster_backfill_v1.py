from typing import List, Optional

from contract.clusters.schemas.cluster_storage_classes import StorageClassContract
from contract.clusters.schemas.cluster_update_v1 import AzureSkuTier, BaseClusterUpdateRequestContractV1
from pydantic import ConfigDict


class ClusterBackfillRequestContractV1(BaseClusterUpdateRequestContractV1):
    """Schema for cluster backfill requests"""

    model_config = ConfigDict(extra="forbid")

    account_name: Optional[str] = None
    subscription: Optional[str] = None
    provider: Optional[str] = None
    internal: Optional[bool] = None
    repository: Optional[str] = None
    network_cidr: Optional[str] = None
    cmdb_app_id: Optional[str] = None
    appd_id: Optional[str] = None
    authorized_api_ip_ranges: Optional[List[str]] = None
    dns_zone: Optional[str] = None
    pod_cidr: Optional[str] = None
    service_cidr: Optional[str] = None
    dns_service_ip: Optional[str] = None
    aws_vpc: Optional[str] = None
    azure_subnet_name: Optional[str] = None
    azure_vnet_name: Optional[str] = None
    azure_vnet_resource_group: Optional[str] = None
    aws_vpc_endpoint_remote_account_ids: Optional[List[str]] = None
    aws_remote_account_ids: Optional[List[str]] = None
    vpc_endpoint_service_name: Optional[str] = None
    vpc_endpoint_service_ingress_name: Optional[str] = None
    cluster_oidc_issuer_url: Optional[str] = None
    azure_sku_tier: Optional[AzureSkuTier] = None
    mi_agentpool_object_id: Optional[str] = None
    mi_cluster_object_id: Optional[str] = None
    storage_classes: Optional[StorageClassContract] = None
