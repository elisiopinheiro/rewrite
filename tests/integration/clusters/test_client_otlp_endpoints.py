import pytest
from factories.cluster_factory import AWSClusterFactory, AzureClusterFactory, make_add_cluster_payload
from factories.otlp_endpoint_factory import ClientOTLPEndpointFactory, make_otlp_endpoint_payload

from api.shared.models.client_otlp_endpoints import EndpointType, OTLPAuthType, OTLPSignal
from api.shared.models.clusters import Provider

INVALID_OTLP_ENDPOINTS = [
    # Non-HTTPS endpoint URL
    {"name": "bad-ep", "type": "otlp", "endpoint": "http://example.com/v1/traces", "signals": ["traces"]},
    # Invalid endpoint type
    {
        "name": "bad-ep",
        "type": "invalid_type",
        "endpoint": "https://example.com/v1/traces",
        "signals": ["traces"],
    },
    # Empty signals list
    {"name": "bad-ep", "type": "otlp", "endpoint": "https://example.com/v1/traces", "signals": []},
    # Invalid signal value
    {
        "name": "bad-ep",
        "type": "otlp",
        "endpoint": "https://example.com/v1/traces",
        "signals": ["invalid_signal"],
    },
    # Invalid auth type
    {
        "name": "bad-ep",
        "type": "otlp",
        "endpoint": "https://example.com/v1/traces",
        "signals": ["traces"],
        "auth": {"type": "invalid", "secret_name": "s", "secret_namespace": "ns"},
    },
    # Auth missing required field secret_name
    {
        "name": "bad-ep",
        "type": "otlp",
        "endpoint": "https://example.com/v1/traces",
        "signals": ["traces"],
        "auth": {"type": "header", "secret_namespace": "ns"},
    },
    # Auth missing required field secret_namespace
    {
        "name": "bad-ep",
        "type": "otlp",
        "endpoint": "https://example.com/v1/traces",
        "signals": ["traces"],
        "auth": {"type": "header", "secret_name": "s"},
    },
    # Auth missing type
    {
        "name": "bad-ep",
        "type": "otlp",
        "endpoint": "https://example.com/v1/traces",
        "signals": ["traces"],
        "auth": {"secret_name": "s", "secret_namespace": "ns"},
    },
    # Auth type header missing header_key
    {
        "name": "bad-ep",
        "type": "otlp",
        "endpoint": "https://example.com/v1/traces",
        "signals": ["traces"],
        "auth": {"type": "header", "secret_name": "s", "secret_namespace": "ns"},
    },
    # Missing required field: name
    {"type": "otlp", "endpoint": "https://example.com/v1/traces", "signals": ["traces"]},
    # Missing required field: type
    {"name": "bad-ep", "endpoint": "https://example.com/v1/traces", "signals": ["traces"]},
    # Missing required field: endpoint
    {"name": "bad-ep", "type": "otlp", "signals": ["traces"]},
    # Missing required field: signals
    {"name": "bad-ep", "type": "otlp", "endpoint": "https://example.com/v1/traces"},
    # Config with empty required_attributes (min_items=1)
    {
        "name": "bad-ep",
        "type": "otlp",
        "endpoint": "https://example.com/v1/traces",
        "signals": ["traces"],
        "config": {"required_attributes": []},
    },
    # Grafana Cloud with auth (must be None)
    {
        "name": "bad-ep",
        "type": "grafanacloud",
        "endpoint": "https://example.com/v1/traces",
        "signals": ["traces"],
        "auth": {"type": "header", "secret_name": "s", "secret_namespace": "ns", "header_key": "X-API-Key"},
    },
    # Grafana Cloud with non-HTTPS endpoint URL
    {
        "name": "bad-ep",
        "type": "grafanacloud",
        "endpoint": "http://example.com/v1/traces",
        "signals": ["traces"],
    },
]


@pytest.mark.integration
@pytest.mark.clusters4wm_app
class TestClientOTLPEndpoints:
    """Integration tests for client OTLP endpoints on clusters."""

    @pytest.mark.client_otlp_endpoints
    class TestAddClusterWithOTLPEndpoints:
        """Tests for OTLP endpoints when creating clusters."""

        def test_add_cluster_without_otlp_endpoints(self, auth_client):
            """Test that client_otlp_endpoints defaults to empty when not provided."""
            cluster_data = make_add_cluster_payload(provider=Provider.AWS)
            cluster_data.pop("client_otlp_endpoints")

            response = auth_client.post("/v1/clusters", json=cluster_data)
            assert response.status_code == 200
            response_data = response.json()
            assert "client_otlp_endpoints" in response_data
            assert response_data["client_otlp_endpoints"] == []

        def test_add_cluster_with_empty_otlp_endpoints(self, auth_client):
            """Test that empty client_otlp_endpoints list is accepted."""
            cluster_data = make_add_cluster_payload(provider=Provider.AWS, client_otlp_endpoints=[])

            response = auth_client.post("/v1/clusters", json=cluster_data)
            assert response.status_code == 200
            assert response.json()["client_otlp_endpoints"] == []

        def test_add_cluster_with_otlp_endpoint(self, auth_client):
            """Test that cluster accepts a valid OTLP endpoint."""
            otlp_endpoint = make_otlp_endpoint_payload(endpoint_type=EndpointType.OTLP)
            cluster_data = make_add_cluster_payload(provider=Provider.AWS, client_otlp_endpoints=[otlp_endpoint])

            response = auth_client.post("/v1/clusters", json=cluster_data)
            assert response.status_code == 200
            endpoints = response.json()["client_otlp_endpoints"]
            assert len(endpoints) == 1
            assert endpoints[0]["name"] == otlp_endpoint["name"]
            assert endpoints[0]["type"] == otlp_endpoint["type"]
            assert endpoints[0]["endpoint"] == otlp_endpoint["endpoint"]
            assert endpoints[0]["signals"] == otlp_endpoint["signals"]

        def test_add_cluster_with_multiple_otlp_endpoints(self, auth_client):
            """Test that cluster accepts multiple OTLP endpoints."""
            grafana_endpoint = make_otlp_endpoint_payload(endpoint_type=EndpointType.GRAFANA_CLOUD)
            endpoints_payload = [
                make_otlp_endpoint_payload(endpoint_type=EndpointType.OTLP),
                make_otlp_endpoint_payload(endpoint_type=EndpointType.SPLUNK),
                grafana_endpoint,
            ]
            cluster_data = make_add_cluster_payload(provider=Provider.AWS, client_otlp_endpoints=endpoints_payload)

            response = auth_client.post("/v1/clusters", json=cluster_data)
            assert response.status_code == 200
            response_endpoints = response.json()["client_otlp_endpoints"]
            assert len(response_endpoints) == 3
            response_names = {ep["name"] for ep in response_endpoints}
            expected_names = {ep["name"] for ep in endpoints_payload}
            assert response_names == expected_names

        @pytest.mark.parametrize("endpoint_type", [EndpointType.OTLP, EndpointType.SPLUNK])
        def test_add_cluster_with_each_endpoint_type(self, auth_client, endpoint_type):
            """Test that each endpoint type (with auth) is accepted."""
            otlp_endpoint = make_otlp_endpoint_payload(endpoint_type=endpoint_type)
            cluster_data = make_add_cluster_payload(provider=Provider.AWS, client_otlp_endpoints=[otlp_endpoint])

            response = auth_client.post("/v1/clusters", json=cluster_data)
            assert response.status_code == 200
            endpoints = response.json()["client_otlp_endpoints"]
            assert len(endpoints) == 1
            assert endpoints[0]["type"] == endpoint_type.value

        def test_add_cluster_with_grafana_cloud_endpoint_type(self, auth_client):
            """Test that Grafana Cloud endpoint type is accepted (without auth)."""
            otlp_endpoint = make_otlp_endpoint_payload(endpoint_type=EndpointType.GRAFANA_CLOUD)
            cluster_data = make_add_cluster_payload(provider=Provider.AWS, client_otlp_endpoints=[otlp_endpoint])

            response = auth_client.post("/v1/clusters", json=cluster_data)
            assert response.status_code == 200
            endpoints = response.json()["client_otlp_endpoints"]
            assert len(endpoints) == 1
            assert endpoints[0]["type"] == "grafanacloud"
            assert endpoints[0]["auth"] is None

        def test_add_cluster_with_otlp_endpoint_multiple_signals(self, auth_client):
            """Test that endpoint accepts multiple signals."""
            otlp_endpoint = make_otlp_endpoint_payload(signals=[OTLPSignal.LOGS.value, OTLPSignal.TRACES.value])
            cluster_data = make_add_cluster_payload(provider=Provider.AWS, client_otlp_endpoints=[otlp_endpoint])

            response = auth_client.post("/v1/clusters", json=cluster_data)
            assert response.status_code == 200
            endpoints = response.json()["client_otlp_endpoints"]
            assert len(endpoints) == 1
            assert set(endpoints[0]["signals"]) == {"logs", "traces"}

        def test_add_cluster_with_otlp_endpoint_all_signals(self, auth_client):
            """Test that endpoint accepts all signal types including metrics."""
            otlp_endpoint = make_otlp_endpoint_payload(
                signals=[OTLPSignal.LOGS.value, OTLPSignal.TRACES.value, OTLPSignal.METRICS.value]
            )
            cluster_data = make_add_cluster_payload(provider=Provider.AWS, client_otlp_endpoints=[otlp_endpoint])

            response = auth_client.post("/v1/clusters", json=cluster_data)
            assert response.status_code == 200
            endpoints = response.json()["client_otlp_endpoints"]
            assert len(endpoints) == 1
            assert set(endpoints[0]["signals"]) == {"logs", "traces", "metrics"}

        def test_add_cluster_with_otlp_endpoint_metrics_signal(self, auth_client):
            """Test that endpoint accepts metrics signal."""
            otlp_endpoint = make_otlp_endpoint_payload(signals=[OTLPSignal.METRICS.value])
            cluster_data = make_add_cluster_payload(provider=Provider.AWS, client_otlp_endpoints=[otlp_endpoint])

            response = auth_client.post("/v1/clusters", json=cluster_data)
            assert response.status_code == 200
            endpoints = response.json()["client_otlp_endpoints"]
            assert len(endpoints) == 1
            assert endpoints[0]["signals"] == ["metrics"]

        def test_add_cluster_with_otlp_endpoint_with_config(self, auth_client):
            """Test that endpoint accepts config with required_attributes."""
            otlp_endpoint = make_otlp_endpoint_payload(
                config={"required_attributes": ["service.name", "deployment.environment"]}
            )
            cluster_data = make_add_cluster_payload(provider=Provider.AWS, client_otlp_endpoints=[otlp_endpoint])

            response = auth_client.post("/v1/clusters", json=cluster_data)
            assert response.status_code == 200
            endpoints = response.json()["client_otlp_endpoints"]
            assert len(endpoints) == 1
            assert endpoints[0]["config"]["required_attributes"] == [
                "service.name",
                "deployment.environment",
            ]

        def test_add_cluster_with_otlp_endpoint_without_auth(self, auth_client):
            """Test that endpoint auth is optional."""
            otlp_endpoint = make_otlp_endpoint_payload(auth=None)
            cluster_data = make_add_cluster_payload(provider=Provider.AWS, client_otlp_endpoints=[otlp_endpoint])

            response = auth_client.post("/v1/clusters", json=cluster_data)
            assert response.status_code == 200
            endpoints = response.json()["client_otlp_endpoints"]
            assert len(endpoints) == 1
            assert endpoints[0]["auth"] is None

        def test_add_cluster_with_otlp_endpoint_without_config(self, auth_client):
            """Test that endpoint config is optional."""
            otlp_endpoint = make_otlp_endpoint_payload()
            cluster_data = make_add_cluster_payload(provider=Provider.AWS, client_otlp_endpoints=[otlp_endpoint])

            response = auth_client.post("/v1/clusters", json=cluster_data)
            assert response.status_code == 200
            endpoints = response.json()["client_otlp_endpoints"]
            assert len(endpoints) == 1
            assert endpoints[0]["config"] is None

        @pytest.mark.parametrize(
            "auth_type",
            [OTLPAuthType.BASIC, OTLPAuthType.HEADER, OTLPAuthType.SPLUNK],
        )
        def test_add_cluster_with_each_auth_type(self, auth_client, auth_type):
            """Test that each auth type is accepted."""
            auth_payload = {
                "type": auth_type.value,
                "secret_name": "my-secret",
                "secret_namespace": "observability",
            }
            if auth_type == OTLPAuthType.HEADER:
                auth_payload["header_key"] = "X-API-Key"

            otlp_endpoint = make_otlp_endpoint_payload(auth=auth_payload)
            cluster_data = make_add_cluster_payload(provider=Provider.AWS, client_otlp_endpoints=[otlp_endpoint])

            response = auth_client.post("/v1/clusters", json=cluster_data)
            assert response.status_code == 200
            endpoints = response.json()["client_otlp_endpoints"]
            assert len(endpoints) == 1
            assert endpoints[0]["auth"]["type"] == auth_type.value

        @pytest.mark.parametrize("invalid_endpoint", INVALID_OTLP_ENDPOINTS)
        def test_add_cluster_with_invalid_otlp_endpoint(self, auth_client, invalid_endpoint):
            """Test that invalid OTLP endpoints are rejected with HTTP 422."""
            cluster_data = make_add_cluster_payload(provider=Provider.AWS, client_otlp_endpoints=[invalid_endpoint])

            response = auth_client.post("/v1/clusters", json=cluster_data)
            assert response.status_code == 422

        def test_add_cluster_with_otlp_endpoint_config_empty_object(self, auth_client):
            """Test that config as empty object is accepted."""
            otlp_endpoint = make_otlp_endpoint_payload(config={})
            cluster_data = make_add_cluster_payload(provider=Provider.AWS, client_otlp_endpoints=[otlp_endpoint])

            response = auth_client.post("/v1/clusters", json=cluster_data)
            assert response.status_code == 200
            endpoints = response.json()["client_otlp_endpoints"]
            assert len(endpoints) == 1

        def test_add_cluster_with_grafana_cloud_endpoint_without_auth(self, auth_client):
            """Test that Grafana Cloud endpoint is accepted without auth."""
            otlp_endpoint = make_otlp_endpoint_payload(endpoint_type=EndpointType.GRAFANA_CLOUD)
            cluster_data = make_add_cluster_payload(provider=Provider.AWS, client_otlp_endpoints=[otlp_endpoint])

            response = auth_client.post("/v1/clusters", json=cluster_data)
            assert response.status_code == 200
            endpoints = response.json()["client_otlp_endpoints"]
            assert len(endpoints) == 1
            assert endpoints[0]["type"] == "grafanacloud"
            assert endpoints[0]["auth"] is None

        def test_add_azure_cluster_with_otlp_endpoint(self, auth_client):
            """Test that Azure cluster also accepts OTLP endpoints."""
            otlp_endpoint = make_otlp_endpoint_payload(endpoint_type=EndpointType.OTLP)
            cluster_data = make_add_cluster_payload(provider=Provider.AZURE, client_otlp_endpoints=[otlp_endpoint])

            response = auth_client.post("/v1/clusters", json=cluster_data)
            assert response.status_code == 200
            endpoints = response.json()["client_otlp_endpoints"]
            assert len(endpoints) == 1
            assert endpoints[0]["name"] == otlp_endpoint["name"]

    @pytest.mark.client_otlp_endpoints
    class TestUpdateClusterOTLPEndpoints:
        """Tests for updating cluster OTLP endpoints."""

        def test_update_cluster_add_otlp_endpoint(self, auth_client):
            """Test adding OTLP endpoints to an existing cluster."""
            cluster = AWSClusterFactory()
            otlp_endpoint = make_otlp_endpoint_payload()

            response = auth_client.put(
                f"/v1/clusters/{cluster.id}",
                json={"client_otlp_endpoints": [otlp_endpoint]},
            )
            assert response.status_code == 200
            endpoints = response.json()["client_otlp_endpoints"]
            assert len(endpoints) == 1
            assert otlp_endpoint.items() <= endpoints[0].items()

        def test_update_cluster_clear_otlp_endpoints(self, auth_client):
            """Test that empty list clears existing OTLP endpoints."""
            cluster = AWSClusterFactory()
            ClientOTLPEndpointFactory(cluster_id=cluster.id)

            response = auth_client.put(
                f"/v1/clusters/{cluster.id}",
                json={"client_otlp_endpoints": []},
            )
            assert response.status_code == 200
            assert response.json()["client_otlp_endpoints"] == []

        def test_update_cluster_replace_otlp_endpoints(self, auth_client):
            """Test replacing existing OTLP endpoints with new ones."""
            cluster = AWSClusterFactory()
            ClientOTLPEndpointFactory(cluster_id=cluster.id, name="old-endpoint")

            new_endpoint = make_otlp_endpoint_payload(name="new-endpoint")

            response = auth_client.put(
                f"/v1/clusters/{cluster.id}",
                json={"client_otlp_endpoints": [new_endpoint]},
            )
            assert response.status_code == 200
            endpoints = response.json()["client_otlp_endpoints"]
            assert len(endpoints) == 1
            assert new_endpoint.items() <= endpoints[0].items()

        def test_update_existing_otlp_endpoint_by_name(self, auth_client):
            """Test updating an existing endpoint matched by name."""
            cluster = AWSClusterFactory()
            ClientOTLPEndpointFactory(
                cluster_id=cluster.id,
                name="my-endpoint",
                type=EndpointType.OTLP.value,
                endpoint="https://old.example.com/v1/traces",
                signals=[OTLPSignal.TRACES.value],
            )

            updated_endpoint = make_otlp_endpoint_payload(
                name="my-endpoint",
                endpoint_type=EndpointType.SPLUNK,
                signals=[OTLPSignal.LOGS.value, OTLPSignal.TRACES.value],
            )

            response = auth_client.put(
                f"/v1/clusters/{cluster.id}",
                json={"client_otlp_endpoints": [updated_endpoint]},
            )
            assert response.status_code == 200
            endpoints = response.json()["client_otlp_endpoints"]
            assert len(endpoints) == 1
            assert updated_endpoint.items() <= endpoints[0].items()

        def test_update_cluster_add_multiple_otlp_endpoints(self, auth_client):
            """Test adding multiple OTLP endpoints at once."""
            cluster = AWSClusterFactory()
            endpoints_payload = [
                make_otlp_endpoint_payload(endpoint_type=EndpointType.OTLP),
                make_otlp_endpoint_payload(endpoint_type=EndpointType.SPLUNK),
            ]

            response = auth_client.put(
                f"/v1/clusters/{cluster.id}",
                json={"client_otlp_endpoints": endpoints_payload},
            )
            assert response.status_code == 200
            endpoints = response.json()["client_otlp_endpoints"]
            assert len(endpoints) == 2
            for payload in endpoints_payload:
                response_ep = next(ep for ep in endpoints if ep["name"] == payload["name"])
                assert payload.items() <= response_ep.items()

        def test_update_cluster_otlp_endpoint_with_config(self, auth_client):
            """Test updating endpoint to include config."""
            cluster = AWSClusterFactory()
            endpoint = make_otlp_endpoint_payload(config={"required_attributes": ["service.name"]})

            response = auth_client.put(
                f"/v1/clusters/{cluster.id}",
                json={"client_otlp_endpoints": [endpoint]},
            )
            assert response.status_code == 200
            endpoints = response.json()["client_otlp_endpoints"]
            assert len(endpoints) == 1
            assert endpoint.items() <= endpoints[0].items()

        def test_update_cluster_otlp_endpoint_without_auth(self, auth_client):
            """Test updating endpoint without auth."""
            cluster = AWSClusterFactory()
            endpoint = make_otlp_endpoint_payload(auth=None)

            response = auth_client.put(
                f"/v1/clusters/{cluster.id}",
                json={"client_otlp_endpoints": [endpoint]},
            )
            assert response.status_code == 200
            endpoints = response.json()["client_otlp_endpoints"]
            assert len(endpoints) == 1
            assert endpoint.items() <= endpoints[0].items()

        @pytest.mark.parametrize("invalid_endpoint", INVALID_OTLP_ENDPOINTS)
        def test_update_cluster_with_invalid_otlp_endpoint(self, auth_client, invalid_endpoint):
            """Test that invalid OTLP endpoints are rejected with HTTP 422."""
            cluster = AWSClusterFactory()
            response = auth_client.put(
                f"/v1/clusters/{cluster.id}",
                json={"client_otlp_endpoints": [invalid_endpoint]},
            )
            assert response.status_code == 422

        def test_update_cluster_otlp_endpoint_config_empty_object(self, auth_client):
            """Test that config as empty object is accepted on update."""
            cluster = AWSClusterFactory()
            endpoint = make_otlp_endpoint_payload(config={})

            response = auth_client.put(
                f"/v1/clusters/{cluster.id}",
                json={"client_otlp_endpoints": [endpoint]},
            )
            assert response.status_code == 200
            endpoints = response.json()["client_otlp_endpoints"]
            assert len(endpoints) == 1
            assert endpoint.items() <= endpoints[0].items()

        def test_update_cluster_grafana_cloud_endpoint_without_auth(self, auth_client):
            """Test that Grafana Cloud endpoint is accepted without auth on update."""
            cluster = AWSClusterFactory()
            endpoint = make_otlp_endpoint_payload(endpoint_type=EndpointType.GRAFANA_CLOUD)

            response = auth_client.put(
                f"/v1/clusters/{cluster.id}",
                json={"client_otlp_endpoints": [endpoint]},
            )
            assert response.status_code == 200
            endpoints = response.json()["client_otlp_endpoints"]
            assert len(endpoints) == 1
            assert endpoint.items() <= endpoints[0].items()

        def test_update_azure_cluster_with_otlp_endpoints(self, auth_client):
            """Test that Azure cluster also supports OTLP endpoint updates."""
            cluster = AzureClusterFactory()
            endpoint = make_otlp_endpoint_payload()

            response = auth_client.put(
                f"/v1/clusters/{cluster.id}",
                json={"client_otlp_endpoints": [endpoint]},
            )
            assert response.status_code == 200
            endpoints = response.json()["client_otlp_endpoints"]
            assert len(endpoints) == 1
            assert endpoint.items() <= endpoints[0].items()

    @pytest.mark.client_otlp_endpoints
    class TestGetClusterOTLPEndpoints:
        """Tests for GET /v1/clusters/{id}/client-otlp-endpoints."""

        def test_get_otlp_endpoints_empty(self, auth_client):
            """Test getting endpoints for a cluster with no OTLP endpoints."""
            cluster = AWSClusterFactory()

            response = auth_client.get(f"/v1/clusters/{cluster.id}/client-otlp-endpoints")
            assert response.status_code == 200
            assert response.json() == []

        def test_get_otlp_endpoints(self, auth_client):
            """Test getting existing OTLP endpoints for a cluster."""
            cluster = AWSClusterFactory()
            endpoint = ClientOTLPEndpointFactory(cluster_id=cluster.id, name="my-endpoint")

            response = auth_client.get(f"/v1/clusters/{cluster.id}/client-otlp-endpoints")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["name"] == "my-endpoint"
            assert data[0]["id"] == endpoint.id

        def test_get_otlp_endpoints_multiple(self, auth_client):
            """Test getting multiple OTLP endpoints."""
            cluster = AWSClusterFactory()
            ClientOTLPEndpointFactory(cluster_id=cluster.id, name="endpoint-1")
            ClientOTLPEndpointFactory(cluster_id=cluster.id, name="endpoint-2")

            response = auth_client.get(f"/v1/clusters/{cluster.id}/client-otlp-endpoints")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            names = {ep["name"] for ep in data}
            assert names == {"endpoint-1", "endpoint-2"}

        def test_get_otlp_endpoints_cluster_not_found(self, auth_client):
            """Test getting endpoints for a non-existent cluster returns 404."""
            response = auth_client.get("/v1/clusters/999999/client-otlp-endpoints")
            assert response.status_code == 404

    @pytest.mark.client_otlp_endpoints
    class TestDeleteOTLPEndpointsViaUpdate:
        """Tests for deleting OTLP endpoints by sending empty list on update."""

        def test_delete_single_otlp_endpoint(self, auth_client):
            """Test removing an endpoint by omitting it from the update list."""
            cluster = AWSClusterFactory()
            ClientOTLPEndpointFactory(cluster_id=cluster.id, name="to-remove")
            ClientOTLPEndpointFactory(cluster_id=cluster.id, name="to-keep")

            keep_endpoint = make_otlp_endpoint_payload(name="to-keep")

            response = auth_client.put(
                f"/v1/clusters/{cluster.id}",
                json={"client_otlp_endpoints": [keep_endpoint]},
            )
            assert response.status_code == 200
            endpoints = response.json()["client_otlp_endpoints"]
            assert len(endpoints) == 1
            assert keep_endpoint.items() <= endpoints[0].items()

        def test_delete_all_otlp_endpoints(self, auth_client):
            """Test removing all endpoints by sending empty list."""
            cluster = AWSClusterFactory()
            ClientOTLPEndpointFactory(cluster_id=cluster.id)
            ClientOTLPEndpointFactory(cluster_id=cluster.id)

            response = auth_client.put(
                f"/v1/clusters/{cluster.id}",
                json={"client_otlp_endpoints": []},
            )
            assert response.status_code == 200
            assert response.json()["client_otlp_endpoints"] == []

            # Verify via GET endpoint as well
            get_response = auth_client.get(f"/v1/clusters/{cluster.id}/client-otlp-endpoints")
            assert get_response.status_code == 200
            assert get_response.json() == []

        def test_otlp_endpoints_not_affected_when_not_in_update(self, auth_client):
            """Test that OTLP endpoints are not removed when not included in the update payload."""
            cluster = AWSClusterFactory()
            ClientOTLPEndpointFactory(cluster_id=cluster.id, name="existing-endpoint")

            # Update a different field, don't include client_otlp_endpoints
            response = auth_client.put(
                f"/v1/clusters/{cluster.id}",
                json={"node_min_count": 2},
            )
            assert response.status_code == 200
            endpoints = response.json()["client_otlp_endpoints"]
            assert len(endpoints) == 1
            assert endpoints[0]["name"] == "existing-endpoint"
