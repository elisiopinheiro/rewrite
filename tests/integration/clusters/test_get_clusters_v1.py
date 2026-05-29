import pytest
from factories.cluster_factory import (
    AdditionalNodePoolFactory,
    AWSClusterFactory,
    AzureClusterFactory,
    TeamsWebhookFactory,
)
from factories.storage_class_factory import RemoteStorageClassFactory, UltraSSDStorageClassFactory

from api.shared.models.clusters import Provider


@pytest.mark.integration
@pytest.mark.clusters4wm_app
class TestGetClustersV1:
    """Integration tests for GET /v1/clusters endpoint."""

    def test_get_clusters_v1(self, auth_client):
        """Test that GET /v1/clusters returns clusters in v1 format."""
        AWSClusterFactory.create_batch(2)
        AzureClusterFactory.create_batch(2)

        response = auth_client.get("/v1/clusters")

        response_data = response.json()
        assert response.status_code == 200
        assert isinstance(response_data, list)
        assert len(response_data) == 4

    @pytest.mark.headlamp_enabled
    class TestHeadlampEnabled:
        """Tests for headlamp_enabled field in GET /v1/clusters response."""

        @pytest.mark.parametrize(
            "headlamp_enabled",
            [True, False],
        )
        def test_get_clusters_v1_returns_headlamp_enabled(self, auth_client, headlamp_enabled):
            """Test that GET /v1/clusters includes headlamp_enabled field."""
            AWSClusterFactory(headlamp_enabled=headlamp_enabled)
            AzureClusterFactory(headlamp_enabled=headlamp_enabled)

            response = auth_client.get("/v1/clusters")

            assert response.status_code == 200
            response_data = response.json()
            assert isinstance(response_data, list)
            assert len(response_data) == 2
            for cluster in response_data:
                assert "headlamp_enabled" in cluster, f"Cluster {cluster.get('name')} is missing headlamp_enabled field"
                assert cluster["headlamp_enabled"] is headlamp_enabled

    @pytest.mark.teams_webhooks
    class TestTeamsWebhooks:
        """Tests for Teams webhooks in GET /v1/clusters response."""

        def test_get_clusters_v1_returns_teams_webhooks(self, auth_client):
            """Test that GET /v1/clusters includes teams_webhooks field."""
            aws_cluster = AWSClusterFactory()
            azure_cluster = AzureClusterFactory()

            TeamsWebhookFactory(cluster=aws_cluster)
            TeamsWebhookFactory(cluster=azure_cluster)

            # Verify teams_webhooks is returned
            response = auth_client.get("/v1/clusters")
            assert response.status_code == 200
            response_data = response.json()
            assert isinstance(response_data, list)
            for cluster in response_data:
                assert "teams_webhooks" in cluster, f"Cluster {cluster.get('name')} is missing teams_webhooks field"
                assert len(cluster["teams_webhooks"]) == 1

    @pytest.mark.storage_classes
    class TestStorageClasses:
        """Tests for storage classes in GET /v1/clusters response."""

        @pytest.mark.remote_storage_classes
        class TestRemoteStorageClasses:
            """Tests for remote storage classes in GET /v1/clusters response."""

            def test_get_clusters_v1_returns_remote_storage_classes(self, auth_client):
                """Test that GET /v1/clusters includes remote_storage_classes field."""
                azure_cluster = AzureClusterFactory()

                RemoteStorageClassFactory(cluster_id=azure_cluster.id)

                # Verify remote_storage_classes is returned
                response = auth_client.get("/v1/clusters")
                assert response.status_code == 200
                response_data = response.json()
                assert isinstance(response_data, list)
                for cluster in response_data:
                    if cluster["provider"] == "azure":
                        assert "storage_classes" in cluster, (
                            f"Cluster {cluster.get('name')} is missing storage_classes field"
                        )
                        assert isinstance(cluster["storage_classes"], dict)
                        assert "remote" in cluster["storage_classes"]

        @pytest.mark.ultra_ssd_storage_classes
        class TestUltraSsdStorageClasses:
            """Tests for Ultra SSD storage classes in GET /v1/clusters response."""

            def test_get_clusters_v1_returns_ultra_ssd_storage_classes(self, auth_client):
                """Test that GET /v1/clusters includes ultra_ssd_storage_classes field."""
                azure_cluster = AzureClusterFactory()

                UltraSSDStorageClassFactory(cluster_id=azure_cluster.id)

                # Verify ultra_ssd_storage_classes is returned
                response = auth_client.get("/v1/clusters")
                assert response.status_code == 200
                response_data = response.json()
                assert isinstance(response_data, list)
                for cluster in response_data:
                    if cluster["provider"] == "azure":
                        assert "storage_classes" in cluster, (
                            f"Cluster {cluster.get('name')} is missing storage_classes field"
                        )
                        assert isinstance(cluster["storage_classes"], dict)
                        assert "ultra_ssd" in cluster["storage_classes"]

    class TestVpcEndpointServiceIngressName:
        """Tests for vpc_endpoint_service_ingress_name in GET /v1/clusters response."""

        def test_get_clusters_v1_returns_vpc_endpoint_service_ingress_name(self, auth_client):
            """Test that GET /v1/clusters includes vpc_endpoint_service_ingress_name field."""
            expected_name = "com.amazonaws.vpce.eu-central-1.vpce-svc-ingress-123456"
            AWSClusterFactory(vpc_endpoint_service_ingress_name=expected_name)

            response = auth_client.get("/v1/clusters")
            assert response.status_code == 200
            response_data = response.json()
            assert isinstance(response_data, list)
            for cluster in response_data:
                if cluster.get("provider") == "aws":
                    assert "vpc_endpoint_service_ingress_name" in cluster, (
                        f"Cluster {cluster.get('name')} is missing vpc_endpoint_service_ingress_name field"
                    )
                    assert cluster["vpc_endpoint_service_ingress_name"] == expected_name

    @pytest.mark.additional_node_pools
    class TestAdditionalNodePools:
        """Tests for additional node pools in GET /v1/clusters response."""

        @pytest.mark.parametrize(
            "provider",
            [Provider.AWS, Provider.AZURE],
        )
        def test_get_clusters_v1_returns_additional_node_pools(self, auth_client, provider):
            """Test that GET /v1/clusters includes additional_node_pools field."""
            cluster = AWSClusterFactory() if provider == Provider.AWS else AzureClusterFactory()
            AdditionalNodePoolFactory(cluster_id=cluster.id)

            # Verify additional_node_pools is returned
            response = auth_client.get("/v1/clusters")
            assert response.status_code == 200
            response_data = response.json()
            assert isinstance(response_data, list)
            for cluster in response_data:
                assert "additional_node_pools" in cluster, (
                    f"Cluster {cluster.get('name')} \
                is missing additional_node_pools field"
                )
                assert isinstance(cluster["additional_node_pools"], list)
                assert len(cluster["additional_node_pools"]) == 1
