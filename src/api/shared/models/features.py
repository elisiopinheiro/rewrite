from collections import Counter
from enum import Enum
from typing import TYPE_CHECKING, Annotated, Dict, List, Optional

from pydantic import (
    AfterValidator,
    ConfigDict,
    PlainSerializer,
    model_validator,
)
from sqlalchemy import Boolean
from sqlmodel import (
    JSON,
    Column,
    Field,
    Relationship,
    SQLModel,
    text,
)

if TYPE_CHECKING:
    from api.shared.models.clusters import ClusterFeature
    from api.shared.models.releases import ReleaseFeature


class FeatureType(str, Enum):
    CORE = "core"
    OPTIONAL = "optional"


class Operator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    IN = "in"
    NOT_IN = "not_in"


class Constraint(SQLModel):
    key: str
    operator: Operator
    value: Optional[str] = None
    values: Optional[List[str]] = None

    @model_validator(mode="before")
    @classmethod
    def compatibility_check(cls, values: dict):
        """Checks the operator and values compatibility"""

        if values.get("operator") in [
            Operator.IN,
            Operator.NOT_IN,
        ]:
            if not values.get("values"):
                raise ValueError("Constraint must include a list of 'values' if the operator is 'in' or 'not_in'")
        elif not values.get("value"):
            raise ValueError("Constraint must include 'value' if the operator is 'equals' or 'not_equals'")
        return values

    def __eq__(self, other):
        if not isinstance(other, Constraint):
            return NotImplemented

        return (
            self.key == other.key
            and self.operator == other.operator
            and self.value == other.value
            and self.values == other.values
        )

    model_config = ConfigDict(arbitrary_types_allowed=True)


LowercasedStr = Annotated[str, AfterValidator(lambda v: v.lower().strip())]
SerializedConstraint = Annotated[
    Constraint,
    AfterValidator(lambda c: dict(c)),
    PlainSerializer(lambda c: c if isinstance(c, dict) else dict(c)),
]


class FeatureBase(SQLModel):
    name: Annotated[str, AfterValidator(lambda v: v.lower().strip())]
    type: Optional[str] = FeatureType.OPTIONAL
    dependencies: Optional[List[LowercasedStr]] = Field(default=None, sa_column=Column(JSON))
    constraints: Optional[List[SerializedConstraint]] = Field(default=None, sa_column=Column(JSON, server_default="[]"))
    namespaced: Optional[bool] = Field(
        default=None, sa_column=Column(Boolean, nullable=False, server_default=text("false"))
    )
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    def dependencies_match(self, other) -> bool:
        if (not self.dependencies) and (not other.dependencies):
            return True
        elif (self.dependencies is None and other.dependencies is not None) or (
            self.dependencies is not None and other.dependencies is None
        ):  # Exclusive or, to ensure length comparison is possible
            return False
        elif len(self.dependencies) != len(other.dependencies):
            return False
        else:
            return Counter(self.dependencies) == Counter(other.dependencies)

    def constraints_match(self, other) -> bool:
        if (not self.constraints) and (not other.constraints):
            return True
        elif (self.constraints is None and other.constraints is not None) or (
            self.constraints is not None and other.constraints is None
        ):  # Exclusive or, to ensure length comparison is possible
            return False
        elif len(self.constraints) != len(other.constraints):
            return False
        else:
            sort_by = "key"
            self_constraints = [
                Constraint(**constraint) for constraint in sorted(self.constraints, key=lambda x: x[sort_by])
            ]

            other_constraints = [
                Constraint(**constraint) for constraint in sorted(other.constraints, key=lambda x: x[sort_by])
            ]

            return self_constraints == other_constraints

    def __eq__(self, other):
        if not isinstance(other, FeatureBase):
            return NotImplemented

        is_equal = True
        if self.name != other.name or self.type != other.type or self.namespaced != other.namespaced:
            is_equal = False
        else:
            is_equal = self.dependencies_match(other) and self.constraints_match(other)

        return is_equal


class FeatureBaseEnable(FeatureBase):
    enabled: Optional[bool] = False
    config: Optional[Dict] = None


class Feature(FeatureBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    clusters: List["ClusterFeature"] = Relationship(
        back_populates="feature",
        sa_relationship_kwargs={
            "cascade": "all",
        },
    )

    releases: List["ReleaseFeature"] = Relationship(
        back_populates="feature",
        sa_relationship_kwargs={
            "cascade": "all",
        },
    )
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
