"""Client namespace schemas."""

from __future__ import annotations

import re
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.core.constants import ADGR_GROUP_REGEX, CONSUMED_BY_REGEX


def _validate_adgr_group_id(value: str) -> str:
    if not re.match(ADGR_GROUP_REGEX, value):
        raise ValueError(f"Group '{value}' is not valid, please check the criteria for the ADGR group ID")
    return value


ValidatedGroup = Annotated[str, AfterValidator(_validate_adgr_group_id)]


class ClientNamespaceWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    consumed_by: Annotated[str, StringConstraints(pattern=CONSUMED_BY_REGEX)] | None = None
    admin: list[ValidatedGroup] = Field(min_length=1)
    viewer: list[ValidatedGroup] | None = None
    editor: list[ValidatedGroup] | None = None

    @field_validator("name")
    @classmethod
    def validate_namespace_name(cls, value: str) -> str:
        if not re.match(r"^(?!-)[a-z0-9-]{1,63}(?<!-)\Z", value):
            raise ValueError(
                f"Namespace '{value}' is not valid, must be between 1 and 63 chars long, "
                "it must consist of lower case alphanumeric characters or -, "
                "and must start and end with an alphanumeric character"
            )
        return value


class ClientNamespaceRead(ClientNamespaceWrite):
    model_config = ConfigDict(extra="forbid")
