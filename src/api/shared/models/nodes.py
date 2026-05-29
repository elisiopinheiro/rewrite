from typing import TYPE_CHECKING, Optional

from pydantic import ConfigDict, StringConstraints, model_validator
from sqlmodel import Column, Field, ForeignKey, Integer, Relationship, SQLModel
from typing_extensions import Annotated

if TYPE_CHECKING:
    from api.shared.models.clusters import Cluster

NAME_REGEX = "^[a-z0-9]{1,12}$"


class AdditionalNodePoolBase(SQLModel):
    name: Annotated[str, StringConstraints(pattern=NAME_REGEX, to_lower=True)]
    node_min_count: Annotated[int, Field(ge=0)]
    node_max_count: Annotated[int, Field(ge=1)]
    tshirt_size: str

    @model_validator(mode="before")
    @classmethod
    def min_max_count_validator(cls, values):
        if isinstance(values, dict):
            min_count = values.get("node_min_count")
            max_count = values.get("node_max_count")
        else:
            min_count = getattr(values, "node_min_count", None)
            max_count = getattr(values, "node_max_count", None)
        if min_count is not None and max_count is not None and min_count > max_count:
            raise ValueError("node_min_count should be less than or equal to node_max_count")
        return values


class AdditionalNodePool(AdditionalNodePoolBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    cluster_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("cluster.id"), index=True),
    )

    cluster: "Cluster" = Relationship(
        back_populates="additional_node_pools",
        sa_relationship_kwargs={"lazy": "joined"},
    )

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
