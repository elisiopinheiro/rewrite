from typing import Dict, List, Optional

import factory
from factory.alchemy import SQLAlchemyModelFactory
from factory.fuzzy import FuzzyChoice
from faker import Faker

from api.shared.models.client_otlp_endpoints import (
    ClientOTLPEndpoint,
    EndpointType,
    OTLPAuthType,
    OTLPSignal,
)

fake = Faker()

_UNSET = object()  # sentinel to distinguish "not provided" from "explicitly None"


class ClientOTLPEndpointFactory(SQLAlchemyModelFactory):
    class Meta:
        model = ClientOTLPEndpoint
        sqlalchemy_session_persistence = "commit"

    name = factory.Sequence(lambda n: f"test-otlp-endpoint-{n}")
    type = FuzzyChoice(EndpointType)
    endpoint = factory.LazyFunction(lambda: f"https://{fake.domain_name()}/v1/traces")
    signals = factory.LazyFunction(lambda: [OTLPSignal.TRACES.value])
    auth = factory.LazyAttribute(
        lambda obj: None
        if obj.type == EndpointType.GRAFANA_CLOUD
        else {
            "type": OTLPAuthType.HEADER.value,
            "secret_name": f"otlp-secret-{fake.word()}",
            "secret_namespace": "observability",
            "header_key": "X-API-Key",
        }
    )
    config = None


def make_otlp_endpoint_payload(
    endpoint_type: EndpointType = EndpointType.OTLP,
    signals: Optional[List[str]] = None,
    auth=_UNSET,
    config: Optional[Dict] = None,
    **overrides,
) -> Dict:
    """Create an OTLP endpoint payload for API testing.

    Args:
        endpoint_type: The endpoint type.
        signals: List of signal types. Defaults to ["traces"].
        auth: Auth configuration dict. Defaults to a header auth for non-Grafana Cloud types.
              Pass None explicitly to omit auth from the payload.
        config: Optional config dict.
        overrides: Additional overrides.

    Returns:
        Dict containing the OTLP endpoint data.
    """
    data = {
        "name": f"otlp-endpoint-{fake.uuid4()[:8]}",
        "type": endpoint_type.value,
        "endpoint": f"https://{fake.domain_name()}/v1/traces",
        "signals": signals or [OTLPSignal.TRACES.value],
    }

    if auth is not _UNSET:
        # Caller explicitly provided auth (could be a dict or None)
        if auth is not None:
            data["auth"] = auth
        # When auth is explicitly None, don't include auth key in payload
    elif endpoint_type != EndpointType.GRAFANA_CLOUD:
        # Default: generate auth for non-Grafana Cloud types
        data["auth"] = {
            "type": OTLPAuthType.HEADER.value,
            "secret_name": f"otlp-secret-{fake.word()}",
            "secret_namespace": "observability",
            "header_key": "X-API-Key",
        }
    # For Grafana Cloud with no explicit auth arg, don't include auth key

    if config is not None:
        data["config"] = config

    data.update(overrides)
    return data
