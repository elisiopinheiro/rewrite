import pytest
from factories.cluster_factory import AWSClusterFactory, AzureClusterFactory
from factories.storage_class_factory import RemoteStorageClassFactory, UltraSSDStorageClassFactory

from api.shared.models.clusters import Provider


@pytest.mark.integration
@pytest.mark.clusters4wm_app
class TestGetClusterById:
    """Integration tests for GET /v1/clusters/{id} endpoint."""

    @pytest.mark.parametrize(
        "provider",
        [Provider.AWS, Provider.AZURE],
    )
    def test_get_cluster_by_id(self, auth_client, provider):
        """Test that GET /v1/clusters/{id} returns cluster details."""
        cluster = AWSClusterFactory() if provider == Provider.AWS else AzureClusterFactory()

        response = auth_client.get(f"/v1/clusters/{cluster.id}")

        response_data = response.json()
        assert response.status_code == 200
        assert isinstance(response_data, dict) and len(response_data)

    @pytest.mark.headlamp_enabled
    class TestHeadlampEnabled:
        """Tests for headlamp_enabled field in GET /v1/clusters/{id} response."""

        @pytest.mark.parametrize(
            "provider, headlamp_enabled",
            [(Provider.AWS, True), (Provider.AZURE, True), (Provider.AWS, False), (Provider.AZURE, False)],
        )
        def test_get_cluster_by_id_returns_headlamp_enabled(self, auth_client, provider, headlamp_enabled):
            """Test that GET /v1/clusters/{id} includes headlamp_enabled field."""
            cluster = (
                AWSClusterFactory(headlamp_enabled=headlamp_enabled)
                if provider == Provider.AWS
                else AzureClusterFactory(headlamp_enabled=headlamp_enabled)
            )

            response = auth_client.get(f"/v1/clusters/{cluster.id}")

            assert response.status_code == 200
            response_data = response.json()
            assert "headlamp_enabled" in response_data, (
                f"Cluster {response_data.get('name')} is missing headlamp_enabled field"
            )
            assert response_data["headlamp_enabled"] is headlamp_enabled

    @pytest.mark.teams_webhooks
    class TestTeamsWebhooks:
        """Tests for Teams webhooks in GET /v1/clusters/{id} response."""

        def test_get_cluster_by_id_returns_teams_webhooks(self, auth_client):
            """Test that GET /v1/clusters/{id} includes teams_webhooks field."""
            cluster = AWSClusterFactory()
            response = auth_client.get(f"/v1/clusters/{cluster.id}")
            assert response.status_code == 200
            response_data = response.json()
            assert "teams_webhooks" in response_data, (
                f"Cluster {response_data.get('name')} is missing teams_webhooks field"
            )

    @pytest.mark.storage_classes
    class TestStorageClasses:
        """Tests for storage classes in GET /v1/clusters/{id} response."""

        @pytest.mark.remote_storage_classes
        class TestRemoteStorageClasses:
            """Tests for remote storage classes in GET /v1/clusters/{id} response."""

            def test_get_cluster_by_id_returns_remote_storage_classes(self, auth_client):
                """Test that GET /v1/clusters/{id} includes remote_storage_classes field."""
                azure_cluster = AzureClusterFactory()
                RemoteStorageClassFactory(cluster_id=azure_cluster.id)

                response = auth_client.get(f"/v1/clusters/{azure_cluster.id}")
                assert response.status_code == 200
                response_data = response.json()
                assert isinstance(response_data, dict)
                assert "storage_classes" in response_data
                assert "remote" in response_data["storage_classes"]
                assert isinstance(response_data["storage_classes"]["remote"], dict)
                assert len(list(response_data["storage_classes"]["remote"].keys())) == 1

        @pytest.mark.ultra_ssd_storage_classes
        class TestUltraSsdStorageClasses:
            """Tests for Ultra SSD storage classes in GET /v1/clusters/{id} response."""

            def test_get_cluster_by_id_returns_ultra_ssd_storage_classes(self, auth_client):
                """Test that GET /v1/clusters/{id} includes ultra_ssd_storage_classes field."""
                azure_cluster = AzureClusterFactory()
                UltraSSDStorageClassFactory(cluster_id=azure_cluster.id)

                response = auth_client.get(f"/v1/clusters/{azure_cluster.id}")
                assert response.status_code == 200
                response_data = response.json()
                assert isinstance(response_data, dict)
                assert "storage_classes" in response_data
                assert "ultra_ssd" in response_data["storage_classes"]
                assert isinstance(response_data["storage_classes"]["ultra_ssd"], dict)
                assert len(list(response_data["storage_classes"]["ultra_ssd"].keys())) == 1

    class TestVpcEndpointServiceIngressName:
        """Tests for vpc_endpoint_service_ingress_name in GET /v1/clusters/{id} response."""

        def test_get_cluster_by_id_returns_vpc_endpoint_service_ingress_name(self, auth_client):
            """Test that GET /v1/clusters/{id} includes vpc_endpoint_service_ingress_name field."""
            expected_name = "com.amazonaws.vpce.eu-central-1.vpce-svc-ingress-123456"
            cluster = AWSClusterFactory(vpc_endpoint_service_ingress_name=expected_name)

            response = auth_client.get(f"/v1/clusters/{cluster.id}")
            assert response.status_code == 200
            response_data = response.json()
            assert "vpc_endpoint_service_ingress_name" in response_data, (
                f"Cluster {response_data.get('name')} is missing vpc_endpoint_service_ingress_name field"
            )
            assert response_data["vpc_endpoint_service_ingress_name"] == expected_name

    @pytest.mark.additional_node_pools
    class TestAdditionalNodePools:
        """Tests for additional node pools in GET /v1/clusters/{id} response."""

        @pytest.mark.parametrize(
            "provider",
            [Provider.AWS, Provider.AZURE],
        )
        def test_get_cluster_by_id_returns_additional_node_pools(self, auth_client, provider):
            """Test that GET /v1/clusters/{id} includes additional_node_pools field."""
            cluster = AWSClusterFactory() if provider == Provider.AWS else AzureClusterFactory()
            response = auth_client.get(f"/v1/clusters/{cluster.id}")
            assert response.status_code == 200
            response_data = response.json()
            assert "additional_node_pools" in response_data, (
                f"Cluster {response_data.get('name')} is missing additional_node_pools field"
            )
            assert isinstance(response_data["additional_node_pools"], list)

    def test_get_cluster_by_id_unauthorized(self, unauth_client):
        """Test that GET /v1/clusters/{id} without credentials returns 401."""
        cluster = AWSClusterFactory()
        response = unauth_client.get(f"/v1/clusters/{cluster.id}")
        assert response.status_code == 401
