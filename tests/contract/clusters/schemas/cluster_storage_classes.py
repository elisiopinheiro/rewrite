"""Storage Classes Contract Models for request and response payloads."""

from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict


class AzureStorageClassSKU(str, Enum):
    STANDARD_LRS = "Standard_LRS"
    PREMIUM_LRS = "Premium_LRS"


class AzureCrossAccountBlobStorageContract(BaseModel):
    """Contract for Azure Cross Account Blob Storage configuration"""

    model_config = ConfigDict(extra="forbid")

    subscription_id: str
    storage_account: str
    resource_group: str
    sku_name: Optional[AzureStorageClassSKU] = AzureStorageClassSKU.STANDARD_LRS
    container: Optional[str] = None


class AzureUltraSSDStorageClassContract(BaseModel):
    """Contract for Azure Ultra SSD Storage Class configuration"""

    model_config = ConfigDict(extra="forbid")

    iops: int
    throughput: int


class StorageClassContract(BaseModel):
    """Contract for storage classes response"""

    model_config = ConfigDict(extra="forbid")

    remote: Optional[Dict[str, AzureCrossAccountBlobStorageContract]] = None
    ultra_ssd: Optional[Dict[str, AzureUltraSSDStorageClassContract]] = None
