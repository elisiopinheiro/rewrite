from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class ProviderType(str, Enum):
    AWS = "aws"
    AZURE = "azure"


class FeatureType(str, Enum):
    CORE = "core"
    OPTIONAL = "optional"


class ConstraintContract(BaseModel):
    """Contract for feature constraints"""

    key: str
    operator: str
    value: Optional[str] = None
    values: Optional[List[str]] = None

    model_config = ConfigDict(extra="forbid")


class FeatureBaseContract(BaseModel):
    """Contract for feature base"""

    name: str
    type: Optional[FeatureType] = FeatureType.OPTIONAL
    dependencies: Optional[List[str]] = None
    constraints: Optional[List[ConstraintContract]] = None

    model_config = ConfigDict(extra="forbid")


class ReleaseResponseContractV1(BaseModel):
    """Release response contract"""

    model_config = ConfigDict(extra="forbid")

    id: int
    name: str
    provider: ProviderType
    reserved_namespaces: Optional[List[str]] = None
    features: Optional[List[FeatureBaseContract]] = None
