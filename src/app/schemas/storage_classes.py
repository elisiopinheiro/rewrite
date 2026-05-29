"""Storage class schemas (Azure only)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import K8S_RESOURCES_NAME_REGEX


class AzureStorageClassSKU(StrEnum):
    STANDARD_LRS = "Standard_LRS"
    PREMIUM_LRS = "Premium_LRS"


class AzureCrossAccountBlobStorage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subscription_id: str
    storage_account: str
    resource_group: str
    sku_name: AzureStorageClassSKU | None = AzureStorageClassSKU.STANDARD_LRS
    container: str | None = Field(default=None, min_length=1, max_length=63, pattern=K8S_RESOURCES_NAME_REGEX)


class AzureUltraSSDStorageClass(BaseModel):
    model_config = ConfigDict(extra="forbid")

    iops: int = Field(ge=1200, le=400000)
    throughput: int = Field(ge=300, le=10000)


class StorageClassPayloadWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    remote: dict[str, AzureCrossAccountBlobStorage] = Field(default_factory=dict)
    ultra_ssd: dict[str, AzureUltraSSDStorageClass] = Field(default_factory=dict)

    def to_entries(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "azure-cross-account-blob-storage",
                "name": name,
                "config": config.model_dump(mode="json", exclude_none=True),
            }
            for name, config in self.remote.items()
        ] + [
            {
                "type": "azure-ultra-ssd",
                "name": name,
                "config": config.model_dump(mode="json", exclude_none=True),
            }
            for name, config in self.ultra_ssd.items()
        ]


class StorageClassPayloadRead(StorageClassPayloadWrite):
    model_config = ConfigDict(extra="forbid")

    @classmethod
    def from_entries(cls, storage_classes: list[Any]) -> StorageClassPayloadRead:
        return cls(
            remote={
                item.name: item.config for item in storage_classes if item.type == "azure-cross-account-blob-storage"
            },
            ultra_ssd={item.name: item.config for item in storage_classes if item.type == "azure-ultra-ssd"},
        )
