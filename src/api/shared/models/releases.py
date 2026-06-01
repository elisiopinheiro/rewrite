from typing import TYPE_CHECKING, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import String as SAString
from sqlmodel import (
    JSON,
    Column,
    Field,
    Relationship,
    SQLModel,
    UniqueConstraint,
)

from api.shared.config import (
    DB_TABLE_RELATIONSHIP_DEFAULTS as RELATIONSHIP_DEFAULTS,
)
from api.shared.enums import Provider
from api.shared.models.features import FeatureBase

if TYPE_CHECKING:
    from api.shared.models.features import Feature


class ReleaseFeature(SQLModel, table=True):
    release_id: Optional[int] = Field(default=None, foreign_key="release.id", primary_key=True)
    feature_id: Optional[int] = Field(default=None, foreign_key="feature.id", primary_key=True)

    release: "Release" = Relationship(
        back_populates="features",
        sa_relationship_kwargs={
            "lazy": "joined",
        },
    )

    feature: "Feature" = Relationship(
        back_populates="releases",
        sa_relationship_kwargs={
            "lazy": "joined",
        },
    )


class ReleaseBase(SQLModel):
    name: str
    provider: Provider = Field(sa_type=SAString)
    reserved_namespaces: Optional[List[str]] = Field(sa_column=Column(JSON), default=[])

    @field_validator("name")
    @classmethod
    def set_name(cls, name):
        return name.lower().strip()

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True, use_enum_values=True)


class Release(ReleaseBase, table=True):
    __table_args__ = (UniqueConstraint("name", "provider", name="release_name_provider_uc"),)
    id: int = Field(default=None, primary_key=True, nullable=False)

    features: Optional[List[ReleaseFeature]] = Relationship(
        back_populates="release",
        sa_relationship_kwargs=RELATIONSHIP_DEFAULTS,
    )
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class ReleaseRequest(ReleaseBase):
    features: Optional[List[FeatureBase]] = None


class ReleaseUpdateRequest(BaseModel):
    features: Optional[List[FeatureBase]] = None
    reserved_namespaces: Optional[List[str]] = None


class ReleaseResponse(ReleaseBase):
    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    features: Optional[List[FeatureBase]] = None

    @staticmethod
    def parse_release(release: Release):
        parsed_release = ReleaseResponse.model_validate(release.model_dump(exclude={"features"}))

        parsed_release.features = [
            FeatureBase.model_validate(release_feature.feature.model_dump()) for release_feature in release.features
        ]

        return parsed_release


OrderByReleaseFields = Literal["id", "name"]
