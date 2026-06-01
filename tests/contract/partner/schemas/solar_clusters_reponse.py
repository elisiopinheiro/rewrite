from typing import List, Optional

from pydantic import BaseModel


class SOLARClusterResponse(BaseModel):
    name: str
    subscription: str
    account_name: str
    provider: str
    multi_tenant: bool
    provider_region: str
    cmdb_app_id: Optional[str] = None
    cmdb_appd_id: Optional[str] = None


class SOLARClusterResponseContract(BaseModel):
    """Schema for a SOLAR cluster response"""

    count: int = 0
    clusters: List[SOLARClusterResponse] = None
