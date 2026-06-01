from datetime import datetime, timedelta, timezone

import pytest
from factories.cluster_factory import (
    AdditionalNodePoolFactory,
    AWSClusterFactory,
    AzureClusterFactory,
    TeamsWebhookFactory,
)
from factories.storage_class_factory import RemoteStorageClassFactory, UltraSSDStorageClassFactory

from api.shared.models.clusters import ClusterLock, Provider


@pytest.mark.integration
@pytest.mark.clusters4wm_app
class TestGetClustersV2:
    """Integration tests for GET /v2/clusters endpoint."""

    def test_get_clusters_v2(self, auth_client):
        """Test that GET /v2/clusters returns clusters in v2 format."""
        AWSClusterFactory.create_batch(2)
        AzureClusterFactory.create_batch(2)

        response = auth_client.get("/v2/clusters")

        response_data = response.json()
        assert response.status_code == 200
        assert isinstance(response_data, dict)
        assert "clusters" in response_data
        assert isinstance(response_data["clusters"], list)
        assert len(response_data["clusters"]) == 4

    @pytest.mark.locked
    class TestLockedField:
        @pytest.mark.parametrize("lock_value", [True, False])
        def test_locked_cluster_returns_expected_value(self, auth_client, lock_value):
            """
            Verify that the API returns the correct locked value from ClusterLock.
            The locked field should match the ClusterLock.locked value when the lock hasn't timed out.
            """

            # Create a cluster and assign a ClusterLock
            cluster = AzureClusterFactory(
                cluster_lock=ClusterLock(
                    locked=lock_value,
                    token="fake-token",
                    owner="test-owner",
                    timeout_at=(datetime.now(tz=timezone.utc) + timedelta(hours=1)).replace(tzinfo=None),
                    created_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
                    updated_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
                )
            )

            # Call the API
            response = auth_client.get("/v2/clusters")
            assert response.status_code == 200

            data = response.json()
            cluster_data = next(c for c in data["clusters"] if c["name"] == cluster.name)

            assert cluster_data["locked"] is lock_value

        def test_expired_lock_returns_false(self, auth_client):
            """
            Verify that the API returns locked=False when the lock has expired.
            If ClusterLock.locked=True but has an expired lock (timeout_at < now) should return False.
            """

            # Create a cluster with an expired lock (timeout in the past)
            cluster = AzureClusterFactory(
                cluster_lock=ClusterLock(
                    locked=True,
                    token="fake-token",
                    owner="test-owner",
                    timeout_at=(datetime.now(tz=timezone.utc) - timedelta(hours=1)).replace(tzinfo=None),
                    created_at=(datetime.now(tz=timezone.utc) - timedelta(hours=2)).replace(tzinfo=None),
                    updated_at=(datetime.now(tz=timezone.utc) - timedelta(hours=1)).replace(tzinfo=None),
                )
            )

            # Call the API
            response = auth_client.get("/v2/clusters")
            assert response.status_code == 200

            data = response.json()
            cluster_data = next(c for c in data["clusters"] if c["name"] == cluster.name)

            # cluster_lock.locked is True but the lock has expired so API should return False
            assert cluster_data["locked"] is False

    @pytest.mark.headlamp_enabled
    class TestHeadlampEnabled:
        """Tests for headlamp_enabled field in GET /v2/clusters response."""

        @pytest.mark.parametrize(
            "headlamp_enabled",
            [True, False],
        )
        def test_get_clusters_v2_returns_headlamp_enabled(self, auth_client, headlamp_enabled):
            """Test that GET /v2/clusters includes headlamp_enabled field."""
            AWSClusterFactory(headlamp_enabled=headlamp_enabled)
            AzureClusterFactory(headlamp_enabled=headlamp_enabled)

            response = auth_client.get("/v2/clusters")

            assert response.status_code == 200
            response_data = response.json()
            assert isinstance(response_data, dict)
            assert "clusters" in response_data
            assert isinstance(response_data["clusters"], list)
            for cluster in response_data["clusters"]:
                assert "headlamp_enabled" in cluster, f"Cluster {cluster.get('name')} is missing headlamp_enabled field"
                assert cluster["headlamp_enabled"] is headlamp_enabled

        class TestHeadlampEnabledFilter:
            """Tests for filtering clusters by headlamp_enabled in GET /v2/clusters."""

            def test_get_clusters_v2_filter_by_headlamp_enabled_true(self, auth_client):
                """Test that GET /v2/clusters can filter by headlamp_enabled=True."""
                AWSClusterFactory(headlamp_enabled=True)
                AzureClusterFactory(headlamp_enabled=False)

                response = auth_client.get("/v2/clusters", params={"headlamp_enabled": True})

                assert response.status_code == 200
                response_data = response.json()
                assert len(response_data["clusters"]) == 1
                assert response_data["clusters"][0]["headlamp_enabled"] is True

            def test_get_clusters_v2_filter_by_headlamp_enabled_false(self, auth_client):
                """Test that GET /v2/clusters can filter by headlamp_enabled=False."""
                AWSClusterFactory(headlamp_enabled=True)
                AzureClusterFactory(headlamp_enabled=False)

                response = auth_client.get("/v2/clusters", params={"headlamp_enabled": False})

                assert response.status_code == 200
                response_data = response.json()
                assert len(response_data["clusters"]) == 1
                assert response_data["clusters"][0]["headlamp_enabled"] is False

    @pytest.mark.teams_webhooks
    class TestTeamsWebhooks:
        """Tests for Teams webhooks in GET /v2/clusters response."""

        def test_get_clusters_v2_returns_teams_webhooks(self, auth_client):
            """Test that GET /v2/clusters includes teams_webhooks field."""
            aws_cluster = AWSClusterFactory()
            azure_cluster = AzureClusterFactory()

            TeamsWebhookFactory(cluster=aws_cluster)
            TeamsWebhookFactory(cluster=azure_cluster)

            # Verify teams_webhooks is returned
            response = auth_client.get("/v2/clusters")
            assert response.status_code == 200
            response_data = response.json()
            assert isinstance(response_data, dict)
            assert "clusters" in response_data
            assert isinstance(response_data["clusters"], list)
            for cluster in response_data["clusters"]:
                assert "teams_webhooks" in cluster, f"Cluster {cluster.get('name')} is missing teams_webhooks field"
                assert len(cluster["teams_webhooks"]) == 1

    @pytest.mark.storage_classes
    class TestRemoteStorageClasses:
        """Tests for storage classes in GET /v2/clusters response."""

        @pytest.mark.remote_storage_classes
        class TestRemoteStorageClasses:
            """Tests for remote storage classes in GET /v2/clusters response."""

            def test_get_clusters_v2_returns_remote_storage_classes(self, auth_client):
                """Test that GET /v2/clusters includes remote_storage_classes for Azure clusters."""
                azure_cluster = AzureClusterFactory()
                aws_cluster = AWSClusterFactory()

                RemoteStorageClassFactory(cluster_id=azure_cluster.id)
                RemoteStorageClassFactory(cluster_id=aws_cluster.id)

                # Verify remote_storage_classes is returned
                response = auth_client.get("/v2/clusters")
                assert response.status_code == 200
                response_data = response.json()
                assert isinstance(response_data, dict)
                assert "clusters" in response_data
                assert isinstance(response_data["clusters"], list)
                for cluster in response_data["clusters"]:
                    if cluster.get("provider") == "azure":
                        assert "storage_classes" in cluster, (
                            f"Cluster {cluster.get('name')} is missing storage_classes field"
                        )
                        assert isinstance(cluster["storage_classes"], dict)
                        assert "remote" in cluster["storage_classes"]
                    else:
                        assert "storage_classes" not in cluster

        @pytest.mark.ultra_ssd_storage_classes
        class TestUltraSsdStorageClasses:
            """Tests for Ultra SSD storage classes in GET /v2/clusters response."""

            def test_get_clusters_v2_returns_ultra_ssd_storage_classes(self, auth_client):
                """Test that GET /v2/clusters includes ultra_ssd_storage_classes for Azure clusters."""
                azure_cluster = AzureClusterFactory()
                aws_cluster = AWSClusterFactory()

                UltraSSDStorageClassFactory(cluster_id=azure_cluster.id)
                UltraSSDStorageClassFactory(cluster_id=aws_cluster.id)

                # Verify ultra_ssd_storage_classes is returned
                response = auth_client.get("/v2/clusters")
                assert response.status_code == 200
                response_data = response.json()
                assert isinstance(response_data, dict)
                assert "clusters" in response_data
                assert isinstance(response_data["clusters"], list)
                for cluster in response_data["clusters"]:
                    if cluster.get("provider") == "azure":
                        assert "storage_classes" in cluster, (
                            f"Cluster {cluster.get('name')} is missing storage_classes field"
                        )
                        assert isinstance(cluster["storage_classes"], dict)
                        assert "ultra_ssd" in cluster["storage_classes"]
                    else:
                        assert "storage_classes" not in cluster

    class TestVpcEndpointServiceIngressName:
        """Tests for vpc_endpoint_service_ingress_name in GET /v2/clusters response."""

        def test_get_clusters_v2_returns_vpc_endpoint_service_ingress_name(self, auth_client):
            """Test that GET /v2/clusters includes vpc_endpoint_service_ingress_name field."""
            expected_name = "com.amazonaws.vpce.eu-central-1.vpce-svc-ingress-123456"
            AWSClusterFactory(vpc_endpoint_service_ingress_name=expected_name)

            response = auth_client.get("/v2/clusters")
            assert response.status_code == 200
            response_data = response.json()
            assert isinstance(response_data, dict)
            assert "clusters" in response_data
            for cluster in response_data["clusters"]:
                if cluster.get("provider") == "aws":
                    assert "vpc_endpoint_service_ingress_name" in cluster, (
                        f"Cluster {cluster.get('name')} is missing vpc_endpoint_service_ingress_name field"
                    )
                    assert cluster["vpc_endpoint_service_ingress_name"] == expected_name

    @pytest.mark.additional_node_pools
    class TestAdditionalNodePools:
        """Tests for additional node pools in GET /v2/clusters response."""

        @pytest.mark.parametrize(
            "provider",
            [Provider.AWS, Provider.AZURE],
        )
        def test_get_clusters_v2_returns_additional_node_pools(self, auth_client, provider):
            """Test that GET /v2/clusters includes additional_node_pools field."""
            cluster = AWSClusterFactory() if provider == Provider.AWS else AzureClusterFactory()
            AdditionalNodePoolFactory(cluster_id=cluster.id)

            # Verify additional_node_pools is returned
            response = auth_client.get("/v2/clusters")
            assert response.status_code == 200
            response_data = response.json()
            assert isinstance(response_data, dict)
            assert "clusters" in response_data
            assert isinstance(response_data["clusters"], list)
            for cluster in response_data["clusters"]:
                assert "additional_node_pools" in cluster, (
                    f"Cluster {cluster.get('name')} is missing additional_node_pools field"
                )
                assert len(cluster["additional_node_pools"]) == 1

    def test_get_clusters_v2_no_clusters_returns_empty_list(self, auth_client):
        """Test that GET /v2/clusters returns 200 with empty ClusterList when no clusters exist."""
        response = auth_client.get("/v2/clusters")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["clusters"] == []

    def test_get_clusters_v2_no_matching_filters_returns_empty_list(self, auth_client):
        """Test that GET /v2/clusters returns 200 with empty ClusterList when no clusters match filters."""
        AWSClusterFactory()

        response = auth_client.get("/v2/clusters", params={"name": "nonexistent-cluster"})
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["clusters"] == []

    def test_get_clusters_v2_invalid_filter_returns_422(self, auth_client):
        """Test that GET /v2/clusters returns 422 for invalid filter values."""
        response = auth_client.get("/v2/clusters", params={"provider": "invalid-provider"})
        assert response.status_code == 422

    def test_get_clusters_v2_invalid_order_by_returns_422(self, auth_client):
        """Test that GET /v2/clusters returns 422 for invalid order_by values."""
        response = auth_client.get("/v2/clusters", params={"order_by": "nonexistent_column"})
        assert response.status_code == 422

    def test_get_clusters_v2_filter_by_locked(self, auth_client):
        """Test that GET /v2/clusters filters by locked status."""
        # Create a locked cluster
        AzureClusterFactory(
            cluster_lock=ClusterLock(
                locked=True,
                token="fake-token",
                owner="test-owner",
                timeout_at=(datetime.now(tz=timezone.utc) + timedelta(hours=1)).replace(tzinfo=None),
                created_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
                updated_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
            )
        )
        # Create an unlocked cluster
        AWSClusterFactory()

        # Filter locked=true
        response = auth_client.get("/v2/clusters", params={"locked": True})
        assert response.status_code == 200
        data = response.json()
        assert all(c["locked"] is True for c in data["clusters"])

    def test_get_clusters_v2_filter_by_unlocked(self, auth_client):
        """Test that GET /v2/clusters filters by unlocked status."""
        # Create a locked cluster
        AzureClusterFactory(
            cluster_lock=ClusterLock(
                locked=True,
                token="fake-token",
                owner="test-owner",
                timeout_at=(datetime.now(tz=timezone.utc) + timedelta(hours=1)).replace(tzinfo=None),
                created_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
                updated_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
            )
        )
        # Create an unlocked cluster
        AWSClusterFactory()

        # Filter locked=false
        response = auth_client.get("/v2/clusters", params={"locked": False})
        assert response.status_code == 200
        data = response.json()
        assert all(c["locked"] is False for c in data["clusters"])

    def test_get_clusters_v2_unauthorized(self, unauth_client):
        """Test that GET /v2/clusters without credentials returns 401."""
        response = unauth_client.get("/v2/clusters")
        assert response.status_code == 401
