"""User feature schemas."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints


class UserFeatureWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Annotated[str, StringConstraints(to_lower=True, strip_whitespace=True)]
    namespace: Annotated[str, StringConstraints(to_lower=True, strip_whitespace=True)]
    repo_url: str
    commit_hash: str
    helm_path: str | None = None
    values_path: str | None = None


class UserFeatureRead(UserFeatureWrite):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
