from typing import List, Optional

from pydantic import BaseModel


class SCPClusterResponse(BaseModel):
    name: str
    subscription: str
    provider_region: str
    azure_vnet_name: str
    azure_vnet_resource_group: str
    network_cidr: str
    cmdb_app_id: Optional[str] = None
    cmdb_appd_id: Optional[str] = None


class SCPClusterResponseContract(BaseModel):
    """Schema for a SCP cluster response"""

    count: int = 0
    clusters: List[SCPClusterResponse] = None
