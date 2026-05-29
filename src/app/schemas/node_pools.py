"""Additional node pool schemas."""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


class AdditionalNodePoolWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Annotated[str, StringConstraints(pattern="^[a-z0-9]{1,12}$", to_lower=True)]
    node_min_count: int = Field(ge=0)
    node_max_count: int = Field(ge=1)
    tshirt_size: str

    @model_validator(mode="before")
    @classmethod
    def validate_min_max_counts(cls, values: Any) -> Any:
        if isinstance(values, dict):
            min_count = values.get("node_min_count")
            max_count = values.get("node_max_count")
        else:
            min_count = getattr(values, "node_min_count", None)
            max_count = getattr(values, "node_max_count", None)
        if min_count is not None and max_count is not None and min_count > max_count:
            raise ValueError("node_min_count should be less than or equal to node_max_count")
        return values


class AdditionalNodePoolRead(AdditionalNodePoolWrite):
    model_config = ConfigDict(extra="forbid")
