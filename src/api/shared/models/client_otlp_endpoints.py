from enum import Enum
from typing import TYPE_CHECKING, Annotated, List, Optional

from pydantic import (
    ConfigDict,
    PlainSerializer,
    ValidationInfo,
    field_validator,
    model_validator,
)
from sqlmodel import JSON, Column, Field, ForeignKey, Integer, Relationship, SQLModel
from sqlmodel.sql.sqltypes import AutoString

from api.shared.models.common import HttpsUrl

if TYPE_CHECKING:
    from api.shared.models.clusters import Cluster


class OTLPAuthType(str, Enum):
    BASIC = "basic"
    HEADER = "header"
    SPLUNK = "splunk"


class EndpointType(str, Enum):
    OTLP = "otlp"
    SPLUNK = "splunk"
    GRAFANA_CLOUD = "grafanacloud"


class OTLPSignal(str, Enum):
    LOGS = "logs"
    TRACES = "traces"
    METRICS = "metrics"


class OTLPConfig(SQLModel):
    required_attributes: Optional[List[str]] = Field(default=None, min_length=1)


class OTLPAuth(SQLModel):
    type: OTLPAuthType
    secret_name: str
    secret_namespace: str
    header_key: Optional[str] = None

    @model_validator(mode="after")
    def validate_header_key(self):
        if self.type == OTLPAuthType.HEADER and not self.header_key:
            raise ValueError("'header_key' is required when auth type is 'header'")
        return self

    model_config = ConfigDict(use_enum_values=True)


SerializedOTLPAuth = Annotated[
    OTLPAuth,
    PlainSerializer(lambda v: v if isinstance(v, dict) else v.model_dump(exclude_unset=True, exclude_none=True)),
]

SerializedOTLPConfig = Annotated[
    OTLPConfig,
    PlainSerializer(lambda v: v if isinstance(v, dict) else v.model_dump(exclude_unset=True, exclude_none=True)),
]


class ClientOTLPEndpointBase(SQLModel):
    name: str
    type: EndpointType = Field(sa_type=AutoString())
    endpoint: HttpsUrl = Field(sa_type=AutoString())
    signals: List[OTLPSignal] = Field(sa_column=Column(JSON, nullable=False), min_length=1)
    auth: Optional[SerializedOTLPAuth] = Field(default=None, sa_column=Column(JSON, nullable=True))
    config: Optional[SerializedOTLPConfig] = Field(default=None, sa_column=Column(JSON, nullable=True))

    # this is a hack ¯\_(ツ)_/¯
    # https://github.com/tiangolo/sqlmodel/issues/63#issuecomment-1008320560
    @field_validator("auth")
    @classmethod
    def val_auth(cls, auth: Optional[OTLPAuth], info: ValidationInfo) -> Optional[dict]:
        if info.data and info.data.get("type") == EndpointType.GRAFANA_CLOUD and auth is not None:
            raise ValueError("auth must be None when endpoint type is grafanacloud")
        if auth:
            return auth.model_dump(exclude_unset=True, exclude_none=True)
        return auth

    @field_validator("config")
    @classmethod
    def val_config(cls, config: Optional[OTLPConfig]) -> Optional[dict]:
        if config:
            return config.model_dump(exclude_unset=True, exclude_none=True)
        return config

    model_config = ConfigDict(use_enum_values=True, arbitrary_types_allowed=True)


class ClientOTLPEndpoint(ClientOTLPEndpointBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    cluster_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("cluster.id"), index=True),
    )

    cluster: "Cluster" = Relationship(
        back_populates="client_otlp_endpoints",
        sa_relationship_kwargs={"lazy": "joined"},
    )

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
