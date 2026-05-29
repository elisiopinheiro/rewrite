import re
from typing import TYPE_CHECKING, List, Optional

from pydantic import AfterValidator, ConfigDict, StringConstraints, field_validator
from sqlmodel import ARRAY, Column, Field, ForeignKey, Integer, Relationship, SQLModel, String
from typing_extensions import Annotated

from api.shared.config import ADGR_GROUP_REGEX, CONSUMED_BY_REGEX

if TYPE_CHECKING:
    from api.shared.models.clusters import Cluster


def _validate_adgr_group_id(v: str) -> str:
    if not re.match(ADGR_GROUP_REGEX, v):
        raise ValueError(f"Group '{v}' is not valid,please check the criteria for the ADGR group ID")
    return v


ValidatedGroup = Annotated[str, AfterValidator(_validate_adgr_group_id)]


class ClientNamespaceBase(SQLModel):
    """ClientNamespaceBase model

    Args:
        SQLModel: Namespace model

    Raises:
        ValueError: Namespace name not valid
        ValueError: Namespace group not valid

    Returns:
        value: namespace
    """

    name: str
    consumed_by: Optional[Annotated[str, StringConstraints(pattern=CONSUMED_BY_REGEX)]] = Field(
        default=None, sa_column=Column(String(), nullable=True)
    )
    admin: List[ValidatedGroup] = Field(sa_column=Column(ARRAY(String()), nullable=False), min_length=1)
    viewer: Optional[List[ValidatedGroup]] = Field(default=None, sa_column=Column(ARRAY(String())))
    editor: Optional[List[ValidatedGroup]] = Field(default=None, sa_column=Column(ARRAY(String())))

    @field_validator("name")
    @classmethod
    def validate_namespace_name(cls, v):
        if not re.match(r"^(?!-)[a-z0-9-]{1,63}(?<!-)$\Z", v):  # noqa
            raise ValueError(
                f"Namespace '{v}' is not valid, must be between 1 and 63 chars long,"
                "it must consist of lower case alphanumeric characters or -,"
                "and must start and end with an alphanumeric character"
            )
        return v


class ClientNamespace(ClientNamespaceBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    cluster_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("cluster.id"), index=True),
    )

    cluster: "Cluster" = Relationship(
        back_populates="client_namespaces",
        sa_relationship_kwargs={"lazy": "joined"},
    )

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
