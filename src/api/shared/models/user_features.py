from typing import TYPE_CHECKING, Annotated, Optional

from pydantic import (
    StringConstraints,
)
from sqlmodel import (
    Field,
    Relationship,
    SQLModel,
)

if TYPE_CHECKING:
    from api.shared.models.clusters import Cluster


class UserFeatureBase(SQLModel):
    name: Annotated[str, StringConstraints(to_lower=True, strip_whitespace=True)] = Field(
        nullable=False, primary_key=True
    )  # noqa
    namespace: Annotated[str, StringConstraints(to_lower=True, strip_whitespace=True)]
    repo_url: str
    commit_hash: str
    helm_path: Optional[str] = None
    values_path: Optional[str] = None


class UserFeature(UserFeatureBase, table=True):
    cluster_id: int = Field(default=None, foreign_key="cluster.id", nullable=False, primary_key=True)

    cluster: "Cluster" = Relationship(
        back_populates="user_features",
        sa_relationship_kwargs={
            "lazy": "noload",
        },
    )
