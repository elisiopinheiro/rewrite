"""Feature schemas for create, read, and cluster-level toggles."""

from collections import Counter
from enum import StrEnum
from typing import Annotated

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, StringConstraints, model_validator


class FeatureType(StrEnum):
    CORE = "core"
    OPTIONAL = "optional"


class FeatureOperator(StrEnum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    IN = "in"
    NOT_IN = "not_in"


class FeatureConstraint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    operator: FeatureOperator
    value: str | None = None
    values: list[str] | None = None

    @model_validator(mode="before")
    @classmethod
    def validate_operator_values(cls, values: dict[str, object]) -> dict[str, object]:
        if values.get("operator") in {FeatureOperator.IN, FeatureOperator.NOT_IN}:
            if not values.get("values"):
                raise ValueError("Constraint must include 'values' for 'in' and 'not_in'")
        elif not values.get("value"):
            raise ValueError("Constraint must include 'value' for 'equals' and 'not_equals'")
        return values


LowercasedStr = Annotated[str, StringConstraints(to_lower=True, strip_whitespace=True)]


class FeatureCreate(BaseModel):
    """Schema for creating a feature (used inside release creation)."""

    model_config = ConfigDict(title="FeatureCreate", extra="forbid")

    name: LowercasedStr
    feature_type: FeatureType = FeatureType.OPTIONAL
    dependencies: list[LowercasedStr] | None = None
    constraints: list[FeatureConstraint] | None = None
    namespaced: bool | None = None

    def dependencies_match(self, other: "FeatureCreate") -> bool:
        if (not self.dependencies) and (not other.dependencies):
            return True
        if (self.dependencies is None) != (other.dependencies is None):
            return False
        return Counter(self.dependencies or []) == Counter(other.dependencies or [])

    def constraints_match(self, other: "FeatureCreate") -> bool:
        if (not self.constraints) and (not other.constraints):
            return True
        if (self.constraints is None) != (other.constraints is None):
            return False
        left = sorted(self.constraints or [], key=lambda item: item.key)
        right = sorted(other.constraints or [], key=lambda item: item.key)
        return left == right


class FeatureRead(FeatureCreate):
    """Feature as returned from the API."""

    id: int
    feature_type: FeatureType = Field(
        default=FeatureType.OPTIONAL,
        validation_alias=AliasChoices("feature_type", "type"),
    )

    model_config = ConfigDict(title="FeatureRead", extra="forbid", from_attributes=True, populate_by_name=True)


class FeatureConfig(BaseModel):
    """Arbitrary feature configuration — allows extra fields."""

    model_config = ConfigDict(title="FeatureConfig", extra="allow")


class FeatureToggleCreate(FeatureCreate):
    """Feature toggle for cluster create/patch — includes enabled + config."""

    enabled: bool = False
    config: FeatureConfig | None = None

    model_config = ConfigDict(title="FeatureToggleCreate", extra="forbid")


class FeatureToggleRead(FeatureRead):
    """Feature toggle as returned on a cluster."""

    enabled: bool = False
    config: FeatureConfig | None = None

    model_config = ConfigDict(title="FeatureToggleRead", extra="forbid")


class FeatureListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    count: int
    items: list[FeatureRead]


class FeatureDeleteResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str
