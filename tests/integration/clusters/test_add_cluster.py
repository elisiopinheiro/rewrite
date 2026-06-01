import pytest
from factories.cluster_factory import make_add_cluster_payload
from factories.feature_factory import make_add_feature_payload
from factories.storage_class_factory import (
    make_add_remote_storage_class_payload,
    make_add_ultra_ssd_storage_class_payload,
)
from utils import popper

from api.shared.models.clusters import Provider


@pytest.mark.integration
@pytest.mark.clusters4wm_app
class TestAddCluster:
    """Integration tests for POST /v1/clusters endpoint."""

    @pytest.mark.parametrize(
        "provider",
        [Provider.AWS, Provider.AZURE],
    )
    def test_add_cluster(self, auth_client, provider):
        """Test that POST /v1/clusters creates a cluster for the given provider."""
        cluster_data = make_add_cluster_payload(provider=provider)

        response = auth_client.post("/v1/clusters", json=cluster_data)

        response_data = response.json()
        # Remove extra fields from the response_data to allow comparison
        popper(response_data, ["id", "created_at", "updated_at", "locked"])
        cluster_data["teams_webhooks"] = []
        assert response.status_code == 200
        assert isinstance(response_data, dict)
        del response_data["is_in_downtime_window"]  # Removing from comparison because it is computed in response-time
        assert response_data == cluster_data

    @pytest.mark.headlamp_enabled
    class TestHeadlampEnabled:
        """Tests for headlamp_enabled field when creating clusters."""

        @pytest.mark.parametrize(
            "provider",
            [Provider.AWS, Provider.AZURE],
        )
        def test_add_cluster_with_headlamp_enabled_true(self, auth_client, provider):
            """Test that POST /v1/clusters accepts headlamp_enabled=True."""
            cluster_data = make_add_cluster_payload(provider=provider, headlamp_enabled=True)

            response = auth_client.post("/v1/clusters", json=cluster_data)

            assert response.status_code == 200
            assert response.json()["headlamp_enabled"] is True

        @pytest.mark.parametrize(
            "provider",
            [Provider.AWS, Provider.AZURE],
        )
        def test_add_cluster_without_headlamp_enabled_defaults_to_false(self, auth_client, provider):
            """Test that headlamp_enabled defaults to False when omitted."""
            cluster_data = make_add_cluster_payload(provider=provider)
            cluster_data.pop("headlamp_enabled")

            response = auth_client.post("/v1/clusters", json=cluster_data)

            assert response.status_code == 200
            assert response.json()["headlamp_enabled"] is False

    @pytest.mark.teams_webhooks
    class TestTeamsWebhooks:
        """Tests for Teams webhooks when creating clusters."""

        def test_add_cluster_without_teams_webhooks(self, auth_client):
            """Test that teams_webhooks field defaults to empty when not provided."""
            cluster_data = make_add_cluster_payload(provider=Provider.AWS)
            # Remove teams_webhooks field
            cluster_data.pop("teams_webhooks")

            response = auth_client.post("/v1/clusters", json=cluster_data)
            assert response.status_code == 200
            response_data = response.json()
            assert "teams_webhooks" in response_data
            assert response_data["teams_webhooks"] == []

        def test_add_cluster_accepts_teams_webhooks(self, auth_client):
            """Test that cluster accepts valid Teams webhooks."""
            webhooks = {
                "customer": {"all": ["https://example.com/webhook1"]},
                "platform": {"all": ["https://example.com/webhook2"]},
            }
            cluster_data = make_add_cluster_payload(provider=Provider.AWS)
            cluster_data["teams_webhooks"] = webhooks

            response = auth_client.post("/v1/clusters", json=cluster_data)
            assert response.status_code == 200
            assert "teams_webhooks" in response.json()
            response_webhooks = response.json()["teams_webhooks"]
            assert len(response_webhooks) == 2

            assert {
                ("customer", "all", "https://example.com/webhook1"),
                ("platform", "all", "https://example.com/webhook2"),
            } == {(wh["type"], wh["level"], wh["url"]) for wh in response_webhooks}

        def test_add_cluster_accepts_empty_teams_webhooks(self, auth_client):
            """Test that empty Teams webhooks object is accepted."""
            cluster_data = make_add_cluster_payload(provider=Provider.AWS)
            cluster_data["teams_webhooks"] = {}

            response = auth_client.post("/v1/clusters", json=cluster_data)
            assert response.status_code == 200
            response_data = response.json()
            assert "teams_webhooks" in response_data
            assert response_data["teams_webhooks"] == []

        @pytest.mark.parametrize(
            "webhooks",
            [
                # Invalid URL
                {"customer": {"all": ["not-a-url"]}},
                # Non-HTTPS URL
                {"customer": {"all": ["http://example.com/webhook1"]}},
                # Duplicate URL in same level
                {"customer": {"all": ["https://example.com/webhook1", "https://example.com/webhook1"]}},
            ],
        )
        def test_add_cluster_with_invalid_webhooks(self, auth_client, webhooks):
            """Test that invalid Teams webhooks are rejected with HTTP 422."""
            cluster_data = make_add_cluster_payload(provider=Provider.AWS)
            cluster_data["teams_webhooks"] = webhooks

            response = auth_client.post("/v1/clusters", json=cluster_data)
            assert response.status_code == 422

    @pytest.mark.optional_features
    class TestOptionalFeatures:
        """Tests for optional features when creating clusters."""

        def test_add_cluster_with_features(self, auth_client):
            """Test that cluster accepts optional features."""
            fake_features = [
                make_add_feature_payload().model_dump(),
                make_add_feature_payload(
                    config={"namespaces": ["namespace1"]},
                    namespaced=True,
                ).model_dump(),
            ]
            release_data = {
                "name": "release-for-cluster-features",
                "provider": Provider.AWS.value,
                "reserved_namespaces": [],
                "features": [
                    {
                        "name": feature["name"],
                        "type": feature["type"],
                        "dependencies": feature.get("dependencies", []),
                        "constraints": feature.get("constraints", []),
                        "namespaced": feature.get("namespaced", False),
                    }
                    for feature in fake_features
                ],
            }
            release_response = auth_client.post("/v1/releases", json=release_data)
            assert release_response.status_code == 200

            cluster_data = make_add_cluster_payload(
                provider=Provider.AWS,
                release=release_data["name"],
                features=fake_features,
            )
            response = auth_client.post("/v1/clusters", json=cluster_data)
            assert response.status_code == 200

    @pytest.mark.storage_classes
    class TestStorageClasses:
        """Tests for storage classes when creating clusters."""

        @pytest.mark.remote_storage_classes
        class TestRemoteStorageClasses:
            """Tests for remote storage classes when creating clusters."""

            @pytest.mark.parametrize(
                "remote_storage_classes",
                [
                    (make_add_remote_storage_class_payload()),
                    ({
                        "remote": {
                            "sg1": {
                                "subscription_id": "subscription-123",
                                "resource_group": "rg-production",
                                "storage_account": "storageacct",
                                "sku_name": "Standard_LRS",
                            }
                        }
                    }),
                    ({}),
                    (None),
                ],
            )
            def test_add_azure_cluster_with_remote_storage_classes(self, auth_client, remote_storage_classes):
                """Test that Azure cluster accepts remote storage classes."""
                cluster_data = make_add_cluster_payload(provider=Provider.AZURE, storage_classes=remote_storage_classes)

                response = auth_client.post("/v1/clusters", json=cluster_data)
                assert response.status_code == 200
                response_storage_classes = response.json()["storage_classes"]["remote"]
                assert isinstance(response_storage_classes, dict) is True
                if remote_storage_classes:
                    assert len(list(response_storage_classes.keys())) == len(list(remote_storage_classes.keys()))

            def test_add_cluster_remote_storage_classes_missing_fields(self, auth_client):
                """Test that remote storage classes with missing required fields are rejected."""
                payload = make_add_remote_storage_class_payload()
                name = list(payload["remote"].keys())[0]
                del payload["remote"][name]["storage_account"]  # required field
                del payload["remote"][name]["sku_name"]
                del payload["remote"][name]["container"]
                remote_storage_classes = payload

                cluster_data = make_add_cluster_payload(provider=Provider.AZURE, storage_classes=remote_storage_classes)

                response = auth_client.post("/v1/clusters", json=cluster_data)
                assert response.status_code == 422

            def test_add_aws_cluster_with_remote_storage_classes(self, auth_client):
                """Test that AWS cluster ignores remote storage classes."""
                cluster_data = make_add_cluster_payload(
                    provider=Provider.AWS,
                    remote_storage_classes=[make_add_remote_storage_class_payload()],
                )

                response = auth_client.post("/v1/clusters", json=cluster_data)
                assert response.status_code == 200
                assert "remote_storage_classes" not in response.json()

        @pytest.mark.ultra_ssd_storage_classes
        class TestUltraSSDStorageClasses:
            """Tests for Ultra SSD storage classes when creating clusters."""

            @pytest.mark.parametrize(
                "ultra_ssd_storage_classes",
                [
                    (make_add_ultra_ssd_storage_class_payload()),
                    ({
                        "ultra_ssd": {
                            "ussg1": {
                                "iops": 4800,
                                "throughput": 1200,
                            }
                        }
                    }),
                    ({}),
                    (None),
                ],
            )
            def test_add_azure_cluster_with_ultra_ssd_storage_classes(self, auth_client, ultra_ssd_storage_classes):
                """Test that Azure cluster accepts Ultra SSD storage classes."""
                cluster_data = make_add_cluster_payload(
                    provider=Provider.AZURE, storage_classes=ultra_ssd_storage_classes
                )

                response = auth_client.post("/v1/clusters", json=cluster_data)
                assert response.status_code == 200
                response_storage_classes = response.json()["storage_classes"]["ultra_ssd"]
                assert isinstance(response_storage_classes, dict) is True
                if ultra_ssd_storage_classes:
                    assert len(list(response_storage_classes.keys())) == len(
                        list(ultra_ssd_storage_classes["ultra_ssd"].keys())
                    )

            def test_add_cluster_ultra_ssd_storage_classes_missing_fields(self, auth_client):
                """Test that Ultra SSD storage classes with missing required fields are rejected."""
                payload = make_add_ultra_ssd_storage_class_payload()
                name = list(payload["ultra_ssd"].keys())[0]
                del payload["ultra_ssd"][name]["iops"]  # required field
                del payload["ultra_ssd"][name]["throughput"]  # required field
                ultra_ssd_storage_classes = payload

                cluster_data = make_add_cluster_payload(
                    provider=Provider.AZURE, storage_classes=ultra_ssd_storage_classes
                )

                response = auth_client.post("/v1/clusters", json=cluster_data)
                assert response.status_code == 422

            def test_add_aws_cluster_with_ultra_ssd_storage_classes(self, auth_client):
                """Test that AWS cluster ignores Ultra SSD storage classes."""
                cluster_data = make_add_cluster_payload(
                    provider=Provider.AWS,
                    ultra_ssd_storage_classes=[make_add_ultra_ssd_storage_class_payload()],
                )

                response = auth_client.post("/v1/clusters", json=cluster_data)
                assert response.status_code == 200
                assert "ultra_ssd_storage_classes" not in response.json()

    @pytest.mark.additional_node_pools
    class TestAdditionalNodePools:
        """Tests for additional node pools when creating clusters."""

        @pytest.mark.parametrize(
            "provider",
            [Provider.AWS, Provider.AZURE],
        )
        def test_add_cluster_without_additional_node_pools(self, auth_client, provider):
            """Test that additional_node_pools field defaults to empty when not provided."""
            cluster_data = make_add_cluster_payload(provider=provider)
            # Remove additional_node_pools field
            del cluster_data["additional_node_pools"]

            response = auth_client.post("/v1/clusters", json=cluster_data)
            assert response.status_code == 200
            response_data = response.json()
            assert "additional_node_pools" in response_data
            assert response_data["additional_node_pools"] == []

        @pytest.mark.parametrize(
            "provider, additional_node_pools",
            [
                (
                    Provider.AWS,
                    [{"name": "nodepool1", "node_min_count": 0, "node_max_count": 1, "tshirt_size": "ram-s"}],
                ),
                (
                    Provider.AZURE,
                    [{"name": "nodepool1", "node_min_count": 0, "node_max_count": 1, "tshirt_size": "ram-s"}],
                ),
                (
                    Provider.AWS,
                    [{"name": "nodepool1", "node_min_count": 1, "node_max_count": 1, "tshirt_size": "ram-s"}],
                ),
                (
                    Provider.AZURE,
                    [{"name": "nodepool1", "node_min_count": 1, "node_max_count": 1, "tshirt_size": "ram-s"}],
                ),
            ],
        )
        def test_add_cluster_accepts_additional_node_pools(self, auth_client, provider, additional_node_pools):
            """Test that cluster accepts valid additional node pools."""
            cluster_data = make_add_cluster_payload(provider=provider, additional_node_pools=additional_node_pools)

            response = auth_client.post("/v1/clusters", json=cluster_data)
            assert response.status_code == 200
            assert "additional_node_pools" in response.json()
            data = response.json()["additional_node_pools"]
            assert len(data) == 1
            assert data == additional_node_pools

        @pytest.mark.parametrize(
            "provider",
            [Provider.AWS, Provider.AZURE],
        )
        def test_add_cluster_accepts_empty_additional_node_pools(self, auth_client, provider):
            """Test that empty additional_node_pools object is accepted."""
            cluster_data = make_add_cluster_payload(provider=provider, additional_node_pools=[])

            response = auth_client.post("/v1/clusters", json=cluster_data)
            assert response.status_code == 200
            assert "additional_node_pools" in response.json()
            assert response.json()["additional_node_pools"] == []

        @pytest.mark.parametrize(
            "provider, additional_node_pools",
            [
                # Invalid name: special characters
                (
                    Provider.AWS,
                    [{"name": "node-pool_1", "node_min_count": 1, "node_max_count": 3, "tshirt_size": "ram-s"}],
                ),
                # Invalid name: too long (max 12 chars)
                (
                    Provider.AZURE,
                    [{"name": "nodepool123456", "node_min_count": 1, "node_max_count": 3, "tshirt_size": "ram-s"}],
                ),
                # Invalid: node_min_count > node_max_count
                (
                    Provider.AWS,
                    [{"name": "nodepool1", "node_min_count": 5, "node_max_count": 3, "tshirt_size": "ram-s"}],
                ),
                # Invalid: node_min_count is negative
                (
                    Provider.AZURE,
                    [{"name": "nodepool1", "node_min_count": -1, "node_max_count": 3, "tshirt_size": "ram-s"}],
                ),
                # Invalid: node_max_count is 0 (should be ge=1)
                (
                    Provider.AWS,
                    [{"name": "nodepool1", "node_min_count": 1, "node_max_count": 0, "tshirt_size": "ram-s"}],
                ),
            ],
        )
        def test_add_cluster_with_invalid_additional_node_pools(self, auth_client, provider, additional_node_pools):
            """Test that invalid additional node pools are rejected with HTTP 422."""
            cluster_data = make_add_cluster_payload(provider=provider, additional_node_pools=additional_node_pools)

            response = auth_client.post("/v1/clusters", json=cluster_data)
            assert response.status_code == 422

    def test_add_cluster_unauthorized(self, unauth_client):
        """Test that creating a cluster without credentials returns 401."""
        cluster_data = make_add_cluster_payload(provider=Provider.AWS)
        response = unauth_client.post("/v1/clusters", json=cluster_data)
        assert response.status_code == 401
