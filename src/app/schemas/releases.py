"""Release schemas — create, read, list."""

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import Provider, ReleaseOrderBy
from app.schemas.features import FeatureCreate, FeatureRead


class ReleaseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    provider: Provider
    reserved_namespaces: list[str] = Field(default_factory=list)
    features: list[FeatureCreate] = Field(default_factory=list)


class ReleaseRead(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    name: str
    provider: Provider
    reserved_namespaces: list[str] = Field(default_factory=list)
    features: list[FeatureRead] = Field(default_factory=list)


class ReleaseListQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    provider: Provider | None = None
    order_by: ReleaseOrderBy = ReleaseOrderBy.ID


class ReleaseListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    count: int
    items: list[ReleaseRead]


class ReleaseDeleteResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str
