import pytest
from factories.cluster_factory import AWSClusterFactory, AzureClusterFactory

from api.shared.models.clusters import ClusterStatus, Provider


@pytest.mark.integration
@pytest.mark.cluster_status
class TestUpdateClustersStatus:
    """Integration tests for PUT /v1/clusters/status endpoint."""

    @pytest.mark.parametrize(
        "provider",
        [Provider.AWS, Provider.AZURE],
    )
    def test_update_clusters_status_success(self, auth_client, provider):
        """Test that PUT /v1/clusters/status updates matching clusters."""
        cluster = (
            AWSClusterFactory(status=ClusterStatus.RUNNING)
            if provider == Provider.AWS
            else AzureClusterFactory(status=ClusterStatus.RUNNING)
        )

        response = auth_client.put(
            "/v1/clusters/status",
            params={"new_status": ClusterStatus.FREEZE.value, "name": cluster.name},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["status"] == ClusterStatus.FREEZE.value

    def test_update_clusters_status_no_matching_clusters(self, auth_client):
        """Test that PUT /v1/clusters/status returns 200 with empty list when no clusters match."""
        response = auth_client.put(
            "/v1/clusters/status",
            params={"new_status": ClusterStatus.FREEZE.value, "name": "nonexistent-cluster"},
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_update_clusters_status_invalid_status_value(self, auth_client):
        """Test that PUT /v1/clusters/status returns 422 for invalid status."""
        cluster = AWSClusterFactory()

        response = auth_client.put(
            "/v1/clusters/status",
            params={"new_status": "invalid-status", "name": cluster.name},
        )
        assert response.status_code == 422

    def test_update_clusters_status_unauthorized(self, unauth_client):
        """Test that PUT /v1/clusters/status returns 401 without credentials."""
        response = unauth_client.put(
            "/v1/clusters/status",
            params={"new_status": ClusterStatus.FREEZE.value},
        )
        assert response.status_code == 401

    def test_get_clusters_status_invalid_order_by_returns_422(self, auth_client):
        """Test that GET /v1/clusters/status returns 422 for invalid order_by values."""
        response = auth_client.get("/v1/clusters/status", params={"order_by": "nonexistent_column"})
        assert response.status_code == 422

    @pytest.mark.parametrize(
        "provider",
        [Provider.AWS, Provider.AZURE],
    )
    @pytest.mark.headlamp_enabled
    def test_update_clusters_status_filtered_by_headlamp_enabled(self, auth_client, provider):
        """Test that PUT /v1/clusters/status filters by headlamp_enabled."""
        cluster_with = (
            AWSClusterFactory(status=ClusterStatus.RUNNING, headlamp_enabled=True)
            if provider == Provider.AWS
            else AzureClusterFactory(status=ClusterStatus.RUNNING, headlamp_enabled=True)
        )
        AWSClusterFactory(
            status=ClusterStatus.RUNNING, headlamp_enabled=False
        ) if provider == Provider.AWS else AzureClusterFactory(status=ClusterStatus.RUNNING, headlamp_enabled=False)

        response = auth_client.put(
            "/v1/clusters/status",
            params={"new_status": ClusterStatus.FREEZE.value, "headlamp_enabled": True},
        )

        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data) == 1
        for cluster in response_data:
            if cluster["headlamp_enabled"]:
                assert cluster["name"] == cluster_with.name
                assert cluster["status"] == ClusterStatus.FREEZE.value
