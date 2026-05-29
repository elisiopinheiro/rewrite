import pytest
from factories.cluster_factory import (
    AdditionalNodePoolFactory,
    AWSClusterFactory,
    AzureClusterFactory,
    ClientNamespaceFactory,
    TeamsWebhookFactory,
)
from factories.storage_class_factory import (
    RemoteStorageClassFactory,
    make_add_remote_storage_class_payload,
    make_add_ultra_ssd_storage_class_payload,
)

from api.shared.models.clusters import Provider


@pytest.mark.integration
@pytest.mark.clusters4wm_app
class TestUpdateCluster:
    """Integration tests for cluster update endpoint."""

    @pytest.mark.parametrize(
        "provider",
        [Provider.AWS, Provider.AZURE],
    )
    def test_update_cluster(self, auth_client, provider):
        """Test that cluster properties can be updated."""
        cluster = AWSClusterFactory() if provider == Provider.AWS else AzureClusterFactory()

        response = auth_client.put(f"/v1/clusters/{cluster.id}", json={"multi_tenant": True})

        assert response.status_code == 200
        assert response.json().get("multi_tenant") is True

    @pytest.mark.headlamp_enabled
    class TestHeadlampEnabled:
        """Tests for updating cluster headlamp_enabled field."""

        @pytest.mark.parametrize(
            "provider, initial, updated",
            [
                (Provider.AWS, False, True),
                (Provider.AWS, True, False),
                (Provider.AZURE, False, True),
                (Provider.AZURE, True, False),
            ],
        )
        def test_update_cluster_headlamp_enabled(self, auth_client, provider, initial, updated):
            """Test that headlamp_enabled can be toggled via PUT."""
            cluster = (
                AWSClusterFactory(headlamp_enabled=initial)
                if provider == Provider.AWS
                else AzureClusterFactory(headlamp_enabled=initial)
            )

            response = auth_client.put(f"/v1/clusters/{cluster.id}", json={"headlamp_enabled": updated})

            assert response.status_code == 200
            assert response.json()["headlamp_enabled"] is updated

        @pytest.mark.parametrize(
            "provider, headlamp_enabled",
            [
                (Provider.AWS, True),
                (Provider.AWS, False),
                (Provider.AZURE, True),
                (Provider.AZURE, False),
            ],
        )
        def test_update_cluster_without_headlamp_enabled_preserves_value(self, auth_client, provider, headlamp_enabled):
            """Test that omitting headlamp_enabled in update doesn't change it."""
            cluster = (
                AWSClusterFactory(headlamp_enabled=headlamp_enabled)
                if provider == Provider.AWS
                else AzureClusterFactory(headlamp_enabled=headlamp_enabled)
            )

            response = auth_client.put(f"/v1/clusters/{cluster.id}", json={"node_min_count": 2})

            assert response.status_code == 200
            assert response.json()["headlamp_enabled"] is headlamp_enabled

    @pytest.mark.teams_webhooks
    class TestTeamsWebhooks:
        """Tests for updating cluster Teams webhooks."""

        def test_update_cluster_without_teams_webhooks(self, auth_client):
            """Test that teams_webhooks field is empty when not provided in update."""
            cluster = AWSClusterFactory()
            response = auth_client.put(f"/v1/clusters/{cluster.id}", json={"node_min_count": 2})
            assert response.status_code == 200
            response_data = response.json()
            assert "teams_webhooks" in response_data
            assert response_data["teams_webhooks"] == []

        def test_update_cluster_accepts_teams_webhooks(self, auth_client):
            """Test that cluster accepts valid Teams webhooks for customer and platform."""
            cluster = AWSClusterFactory()

            new_webhooks = {
                "customer": {"all": ["https://example.com/webhook1"]},
                "platform": {"all": ["https://example.com/webhook2"]},
            }

            response = auth_client.put(f"/v1/clusters/{cluster.id}", json={"teams_webhooks": new_webhooks})
            assert response.status_code == 200
            assert "teams_webhooks" in response.json()
            response_webhooks = response.json()["teams_webhooks"]
            assert len(response_webhooks) == 2

            assert {
                ("customer", "all", "https://example.com/webhook1"),
                ("platform", "all", "https://example.com/webhook2"),
            } == {(wh["type"], wh["level"], wh["url"]) for wh in response_webhooks}

        def test_update_cluster_accepts_empty_teams_webhooks(self, auth_client):
            """Test that empty Teams webhooks object clears existing webhooks."""
            cluster = AWSClusterFactory()
            TeamsWebhookFactory(cluster=cluster)

            response = auth_client.put(f"/v1/clusters/{cluster.id}", json={"teams_webhooks": {}})
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
        def test_update_cluster_with_invalid_webhooks(self, auth_client, webhooks):
            """Test that invalid Teams webhooks are rejected with HTTP 422."""
            cluster = AWSClusterFactory()
            response = auth_client.put(f"/v1/clusters/{cluster.id}", json={"teams_webhooks": webhooks})
            assert response.status_code == 422

    @pytest.mark.client_namespaces
    class TestClientNamespaces:
        """Tests for updating cluster client namespaces."""

        def test_update_cluster_with_client_namespaces(self, auth_client):
            """Test that cluster accepts client namespaces with consumed_by."""
            cluster = AWSClusterFactory()

            client_namespaces = [
                {
                    "name": "test-namespace-1",
                    "consumed_by": "APPD-123456",
                    "admin": ["APPL_4WM_admin"],
                    "viewer": ["APPL_4WM_viewer"],
                    "editor": ["APPL_4WM_editor"],
                }
            ]

            response = auth_client.put(f"/v1/clusters/{cluster.id}", json={"client_namespaces": client_namespaces})
            assert response.status_code == 200
            assert "client_namespaces" in response.json()
            response_namespaces = response.json()["client_namespaces"]
            assert len(response_namespaces) == 1
            assert client_namespaces[0].items() <= response_namespaces[0].items()

        def test_update_cluster_with_client_namespaces_without_consumed_by(self, auth_client):
            """Test that consumed_by is optional in client namespaces."""
            cluster = AWSClusterFactory()

            client_namespaces = [
                {
                    "name": "test-namespace-2",
                    "admin": ["APPL_4WM_admin"],
                }
            ]

            response = auth_client.put(f"/v1/clusters/{cluster.id}", json={"client_namespaces": client_namespaces})
            assert response.status_code == 200
            response_namespaces = response.json()["client_namespaces"]
            assert len(response_namespaces) == 1
            assert client_namespaces[0].items() <= response_namespaces[0].items()

        def test_update_existing_namespace_with_consumed_by(self, auth_client):
            """Test updating existing namespace to add consumed_by."""
            cluster = AWSClusterFactory()
            namespace = ClientNamespaceFactory(cluster_id=cluster.id, consumed_by=None)

            client_namespaces = [
                {
                    "name": namespace.name,
                    "consumed_by": "APPD-999999",
                    "admin": namespace.admin,
                }
            ]

            response = auth_client.put(f"/v1/clusters/{cluster.id}", json={"client_namespaces": client_namespaces})
            assert response.status_code == 200
            response_namespaces = response.json()["client_namespaces"]
            assert len(response_namespaces) == 1
            assert client_namespaces[0].items() <= response_namespaces[0].items()

        def test_update_cluster_with_invalid_consumed_by(self, auth_client):
            """Test that consumed_by must start with APPD."""
            cluster = AWSClusterFactory()

            client_namespaces = [
                {
                    "name": "test-namespace",
                    "consumed_by": "INVALID123",
                    "admin": ["APPL_4WM_admin"],
                }
            ]

            response = auth_client.put(f"/v1/clusters/{cluster.id}", json={"client_namespaces": client_namespaces})
            assert response.status_code == 422

    @pytest.mark.storage_classes
    class TestStorageClasses:
        """Tests for updating cluster storage classes."""

        @pytest.mark.remote_storage_classes
        class TestRemoteStorageClasses:
            """Tests for updating cluster remote storage classes."""

            @pytest.mark.parametrize(
                "remote_storage_classes",
                [
                    (make_add_remote_storage_class_payload() | make_add_remote_storage_class_payload()),
                    ({
                        "remote": {
                            "sg1": {
                                "subscription_id": "subscription-123",
                                "resource_group": "rg-production",
                                "storage_account": "storageacct",
                            }
                        }
                    }),
                    ({}),
                    (None),
                ],
            )
            def test_update_cluster_remote_storage_classes(self, auth_client, remote_storage_classes):
                """Test that cluster accepts valid remote storage classes configuration."""
                cluster = AzureClusterFactory()
                response = auth_client.put(
                    f"/v1/clusters/{cluster.id}", json={"storage_classes": remote_storage_classes}
                )
                assert response.status_code == 200
                response_storage_classes = response.json()["storage_classes"]["remote"]
                assert isinstance(response_storage_classes, dict) is True
                if remote_storage_classes and remote_storage_classes.get("remote"):
                    for name, config in remote_storage_classes["remote"].items():
                        assert name in response_storage_classes
                        assert config.items() <= response_storage_classes[name].items()

            def test_update_cluster_remote_storage_classes_missing_fields(self, auth_client):
                """Test that remote storage classes with missing required fields are rejected."""
                cluster = AzureClusterFactory()
                payload = make_add_remote_storage_class_payload()
                name = list(payload["remote"].keys())[0]
                del payload["remote"][name]["storage_account"]  # required field
                del payload["remote"][name]["sku_name"]
                del payload["remote"][name]["container"]
                remote_storage_classes = payload

                response = auth_client.put(
                    f"/v1/clusters/{cluster.id}", json={"storage_classes": remote_storage_classes}
                )
                assert response.status_code == 422

            def test_update_existing_remote_storage_class_by_name(self, auth_client):
                """Test updating an existing remote storage class matched by name."""
                cluster = AzureClusterFactory()
                RemoteStorageClassFactory(cluster_id=cluster.id, name="my-sc")

                updated_config = {
                    "subscription_id": "new-sub-123",
                    "resource_group": "new-rg",
                    "storage_account": "newstorage",
                }

                response = auth_client.put(
                    f"/v1/clusters/{cluster.id}",
                    json={"storage_classes": {"remote": {"my-sc": updated_config}}},
                )
                assert response.status_code == 200
                remote = response.json()["storage_classes"]["remote"]
                assert "my-sc" in remote
                assert updated_config.items() <= remote["my-sc"].items()

        @pytest.mark.ultra_ssd_storage_classes
        class TestUltraSsdStorageClasses:
            """Tests for updating cluster Ultra SSD storage classes."""

            @pytest.mark.parametrize(
                "ultra_ssd_storage_classes",
                [
                    (make_add_ultra_ssd_storage_class_payload() | make_add_ultra_ssd_storage_class_payload()),
                    ({
                        "ultra_ssd": {
                            "ussg1": {
                                "iops": 5000,
                                "throughput": 500,
                            }
                        }
                    }),
                    ({}),
                    (None),
                ],
            )
            def test_update_cluster_ultra_ssd_storage_classes(self, auth_client, ultra_ssd_storage_classes):
                """Test that cluster accepts valid Ultra SSD storage classes configuration."""
                cluster = AzureClusterFactory()
                response = auth_client.put(
                    f"/v1/clusters/{cluster.id}", json={"storage_classes": ultra_ssd_storage_classes}
                )
                assert response.status_code == 200
                response_storage_classes = response.json()["storage_classes"]["ultra_ssd"]
                assert isinstance(response_storage_classes, dict) is True
                if ultra_ssd_storage_classes and ultra_ssd_storage_classes.get("ultra_ssd"):
                    for name, config in ultra_ssd_storage_classes["ultra_ssd"].items():
                        assert name in response_storage_classes
                        assert config.items() <= response_storage_classes[name].items()

            def test_update_cluster_ultra_ssd_storage_classes_missing_fields(self, auth_client):
                """Test that Ultra SSD storage classes with missing required fields are rejected."""
                cluster = AzureClusterFactory()
                payload = make_add_ultra_ssd_storage_class_payload()
                name = list(payload["ultra_ssd"].keys())[0]
                del payload["ultra_ssd"][name]["iops"]  # required field
                del payload["ultra_ssd"][name]["throughput"]  # required field
                ultra_ssd_storage_classes = payload

                response = auth_client.put(
                    f"/v1/clusters/{cluster.id}", json={"storage_classes": ultra_ssd_storage_classes}
                )
                assert response.status_code == 422

    @pytest.mark.additional_node_pools
    class TestAdditionalNodePools:
        """Tests for updating cluster additional node pools."""

        @pytest.mark.parametrize(
            "provider",
            [Provider.AWS, Provider.AZURE],
        )
        def test_update_cluster_without_additional_node_pools(self, auth_client, provider):
            """Test that additional_node_pools field is empty when not provided in update."""
            cluster = AWSClusterFactory() if provider == Provider.AWS else AzureClusterFactory()
            response = auth_client.put(f"/v1/clusters/{cluster.id}", json={"node_min_count": 2})
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
        def test_update_cluster_accepts_additional_node_pools(self, auth_client, provider, additional_node_pools):
            """Test that cluster accepts valid additional node pools configuration."""
            cluster = AWSClusterFactory() if provider == Provider.AWS else AzureClusterFactory()

            response = auth_client.put(
                f"/v1/clusters/{cluster.id}", json={"additional_node_pools": additional_node_pools}
            )
            assert response.status_code == 200
            assert "additional_node_pools" in response.json()
            data = response.json()["additional_node_pools"]
            assert len(data) == len(additional_node_pools)
            assert data == additional_node_pools

        @pytest.mark.parametrize(
            "provider",
            [Provider.AWS, Provider.AZURE],
        )
        def test_update_cluster_accepts_empty_additional_node_pools(self, auth_client, provider):
            """Test that empty additional node pools object clears existing node pools."""
            cluster = AWSClusterFactory() if provider == Provider.AWS else AzureClusterFactory()
            AdditionalNodePoolFactory(cluster=cluster)

            response = auth_client.put(f"/v1/clusters/{cluster.id}", json={"additional_node_pools": []})
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
        def test_update_cluster_with_invalid_additional_node_pools(self, auth_client, provider, additional_node_pools):
            """Test that invalid additional node pools are rejected with HTTP 422."""
            cluster = AWSClusterFactory() if provider == Provider.AWS else AzureClusterFactory()
            response = auth_client.put(
                f"/v1/clusters/{cluster.id}", json={"additional_node_pools": additional_node_pools}
            )
            assert response.status_code == 422

        def test_update_existing_additional_node_pool_by_name(self, auth_client):
            """Test updating an existing node pool matched by name."""
            cluster = AWSClusterFactory()
            AdditionalNodePoolFactory(
                cluster_id=cluster.id,
                name="nodepool1",
                node_min_count=0,
                node_max_count=1,
                tshirt_size="ram-s",
            )

            updated_node_pool = {
                "name": "nodepool1",
                "node_min_count": 1,
                "node_max_count": 5,
                "tshirt_size": "ram-s",
            }

            response = auth_client.put(
                f"/v1/clusters/{cluster.id}",
                json={"additional_node_pools": [updated_node_pool]},
            )
            assert response.status_code == 200
            node_pools = response.json()["additional_node_pools"]
            assert len(node_pools) == 1
            assert node_pools[0] == updated_node_pool

    def test_update_cluster_not_found(self, auth_client):
        """Test that updating a non-existent cluster returns 404."""
        response = auth_client.put("/v1/clusters/999999", json={"multi_tenant": True})
        assert response.status_code == 404
        assert response.json()["detail"] == "Cluster not found"

    def test_update_cluster_unauthorized(self, unauth_client):
        """Test that updating a cluster without credentials returns 401."""
        cluster = AWSClusterFactory()
        response = unauth_client.put(f"/v1/clusters/{cluster.id}", json={"multi_tenant": True})
        assert response.status_code == 401
