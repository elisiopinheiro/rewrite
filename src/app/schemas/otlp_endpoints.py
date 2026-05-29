"""Client OTLP endpoint schemas."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.types import HttpsUrl


class OTLPAuthType(StrEnum):
    BASIC = "basic"
    HEADER = "header"
    SPLUNK = "splunk"


class EndpointType(StrEnum):
    OTLP = "otlp"
    SPLUNK = "splunk"
    GRAFANA_CLOUD = "grafanacloud"


class OTLPSignal(StrEnum):
    LOGS = "logs"
    TRACES = "traces"
    METRICS = "metrics"


class OTLPConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    required_attributes: list[str] | None = Field(default=None, min_length=1)


class OTLPAuth(BaseModel):
    model_config = ConfigDict(extra="forbid")

    auth_type: OTLPAuthType
    secret_name: str
    secret_namespace: str


class ClientOTLPEndpointWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    endpoint_type: EndpointType
    endpoint: HttpsUrl
    signals: list[OTLPSignal] = Field(min_length=1)
    auth: OTLPAuth | None = None
    config: OTLPConfig | None = None

    @field_validator("auth")
    @classmethod
    def validate_auth(cls, auth: OTLPAuth | None, info: Any) -> OTLPAuth | None:
        endpoint_type = info.data.get("endpoint_type") if info.data else None
        if endpoint_type == EndpointType.GRAFANA_CLOUD and auth is not None:
            raise ValueError("auth must be None when endpoint type is grafanacloud")
        return auth


class ClientOTLPEndpointRead(ClientOTLPEndpointWrite):
    model_config = ConfigDict(extra="forbid")
