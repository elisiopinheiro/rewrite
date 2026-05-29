from enum import Enum
from typing import TYPE_CHECKING, Annotated, Dict, List, Optional, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    PlainSerializer,
    StringConstraints,
    field_validator,
)
from pydantic import Field as PydanticField
from sqlalchemy import String as SAString
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import (
    Column,
    Field,
    ForeignKey,
    Integer,
    Relationship,
    SQLModel,
)

from api.shared.config import K8S_RESOURCES_NAME_REGEX

if TYPE_CHECKING:
    from api.shared.models.clusters import Cluster


class StorageClassType(str, Enum):
    AZ_CABS = "azure-cross-account-blob-storage"
    AZ_USSD = "azure-ultra-ssd"


class AzureStorageClassSKU(str, Enum):
    STANDARD_LRS = "Standard_LRS"
    PREMIUM_LRS = "Premium_LRS"


class AzureCrossAccountBlobStorage(BaseModel):
    subscription_id: str
    storage_account: str
    resource_group: str
    sku_name: Optional[AzureStorageClassSKU] = AzureStorageClassSKU.STANDARD_LRS
    container: Optional[str] = PydanticField(
        default=None, min_length=1, max_length=63, pattern=K8S_RESOURCES_NAME_REGEX
    )


class AzureUltraSSDStorageClass(BaseModel):
    iops: int = PydanticField(ge=1200, le=400000)
    throughput: int = PydanticField(ge=300, le=10000)


SerializedStorageClassConfig = Annotated[
    Union[AzureCrossAccountBlobStorage, AzureUltraSSDStorageClass],
    PlainSerializer(lambda v: v if isinstance(v, dict) else v.model_dump()),
]


class StorageClassBase(SQLModel):
    type: StorageClassType = Field(sa_type=SAString, nullable=False)
    name: Annotated[str, StringConstraints(min_length=1, max_length=63, pattern=K8S_RESOURCES_NAME_REGEX)] = Field(
        nullable=False
    )
    config: SerializedStorageClassConfig = Field(sa_column=Column(JSONB, nullable=False))

    @field_validator("config")
    @classmethod
    def serialize_config(cls, v):
        """Serialize config to dict."""
        return v.model_dump()

    model_config = ConfigDict(arbitrary_types_allowed=True, use_enum_values=True)


class StorageClass(StorageClassBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    cluster_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("cluster.id", ondelete="CASCADE"), nullable=False, index=True),
    )

    cluster: "Cluster" = Relationship(
        back_populates="storage_classes",
        sa_relationship_kwargs={"lazy": "joined"},
    )
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class StorageClassPayload(BaseModel):
    """Model for request and response"""

    remote: Optional[Dict[str, AzureCrossAccountBlobStorage]] = {}
    ultra_ssd: Optional[Dict[str, AzureUltraSSDStorageClass]] = {}

    @classmethod
    def from_list(cls, storage_classes: List[StorageClass]) -> "StorageClassPayload":
        """Build a StorageClassPayload model from a list of StorageClass DB objects."""
        return cls(
            remote={sc.name: sc.config for sc in storage_classes if sc.type == StorageClassType.AZ_CABS},
            ultra_ssd={sc.name: sc.config for sc in storage_classes if sc.type == StorageClassType.AZ_USSD},
        )

    def to_list(self) -> List[StorageClassBase]:
        """Convert StorageClassPayload model to a list of StorageClassBase objects."""
        return [
            StorageClassBase(type=StorageClassType.AZ_CABS, name=name, config=config)
            for name, config in self.remote.items()
        ] + [
            StorageClassBase(type=StorageClassType.AZ_USSD, name=name, config=config)
            for name, config in self.ultra_ssd.items()
        ]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "remote": {
                    "my-storage-class": {
                        "subscription_id": "12345678-1234-1234-1234-123456789012",
                        "storage_account": "mystorageaccount",
                        "resource_group": "my-resource-group",
                        "sku_name": "Standard_LRS",
                    }
                },
                "ultra_ssd": {"my-ultra-ssd": {"iops": 1200, "throughput": 300}},
            }
        }
    )
