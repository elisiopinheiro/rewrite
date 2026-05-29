import pytest
from factories.cluster_factory import AWSClusterFactory


@pytest.mark.integration
@pytest.mark.clusters4wm_app
class TestGetOperationsV1:
    """Integration tests for GET /v1/operations endpoint."""

    def test_get_operations_v1_returns_all(self, auth_client):
        """Test that GET /v1/operations returns all operations."""
        cluster = AWSClusterFactory()

        auth_client.post(
            f"/v1/clusters/{cluster.id}/operations",
            json={"type": "deploy", "status": "completed", "cicd_url": "https://example.com/1"},
        )
        auth_client.post(
            f"/v1/clusters/{cluster.id}/operations",
            json={"type": "destroy", "status": "in_progress", "cicd_url": "https://example.com/2"},
        )

        response = auth_client.get("/v1/operations")
        assert response.status_code == 200

        response_data = response.json()
        assert isinstance(response_data, list)
        assert len(response_data) == 2

    def test_get_operations_v1_empty_database_returns_404(self, auth_client):
        """Test that GET /v1/operations returns 404 when no operations exist."""
        response = auth_client.get("/v1/operations")
        assert response.status_code == 404
        assert response.json()["detail"] == "Operation not found"

    def test_get_operations_v1_no_matching_filter_returns_404(self, auth_client):
        """Test that GET /v1/operations returns 404 when no operations match filter."""
        cluster = AWSClusterFactory()

        auth_client.post(
            f"/v1/clusters/{cluster.id}/operations",
            json={"type": "deploy", "status": "completed", "cicd_url": "https://example.com/1"},
        )

        response = auth_client.get("/v1/operations?type=nonexistent")
        assert response.status_code == 404
        assert response.json()["detail"] == "Operation not found"
