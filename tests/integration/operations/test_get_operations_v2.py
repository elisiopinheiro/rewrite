import pytest
from factories.cluster_factory import AWSClusterFactory


@pytest.mark.integration
@pytest.mark.clusters4wm_app
class TestGetOperationsV2:
    """Integration tests for GET /v2/operations endpoint."""

    def test_get_operations_v2_returns_all(self, auth_client):
        """Test that GET /v2/operations returns all operations."""
        cluster = AWSClusterFactory()

        # Create operations via the API
        operation_data = {"type": "deploy", "status": "completed", "cicd_url": "https://example.com/1"}
        auth_client.post(f"/v1/clusters/{cluster.id}/operations", json=operation_data)
        operation_data = {"type": "destroy", "status": "in_progress", "cicd_url": "https://example.com/2"}
        auth_client.post(f"/v1/clusters/{cluster.id}/operations", json=operation_data)

        response = auth_client.get("/v2/operations")
        assert response.status_code == 200

        response_data = response.json()
        assert isinstance(response_data, list)
        assert len(response_data) == 2

    def test_get_operations_v2_filter_by_type(self, auth_client):
        """Test that GET /v2/operations can filter by type."""
        cluster = AWSClusterFactory()

        auth_client.post(
            f"/v1/clusters/{cluster.id}/operations",
            json={"type": "deploy", "status": "completed", "cicd_url": "https://example.com/1"},
        )
        auth_client.post(
            f"/v1/clusters/{cluster.id}/operations",
            json={"type": "destroy", "status": "completed", "cicd_url": "https://example.com/2"},
        )

        response = auth_client.get("/v2/operations?type=deploy")
        assert response.status_code == 200

        response_data = response.json()
        assert isinstance(response_data, list)
        assert len(response_data) == 1
        assert response_data[0]["type"] == "deploy"

    def test_get_operations_v2_filter_by_status(self, auth_client):
        """Test that GET /v2/operations can filter by status."""
        cluster = AWSClusterFactory()

        auth_client.post(
            f"/v1/clusters/{cluster.id}/operations",
            json={"type": "deploy", "status": "completed", "cicd_url": "https://example.com/1"},
        )
        auth_client.post(
            f"/v1/clusters/{cluster.id}/operations",
            json={"type": "deploy", "status": "in_progress", "cicd_url": "https://example.com/2"},
        )

        response = auth_client.get("/v2/operations?status=completed")
        assert response.status_code == 200

        response_data = response.json()
        assert isinstance(response_data, list)
        assert len(response_data) == 1
        assert response_data[0]["status"] == "completed"

    def test_get_operations_v2_empty_database(self, auth_client):
        """Test that GET /v2/operations returns 200 with empty list when no operations exist."""
        response = auth_client.get("/v2/operations")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_operations_v2_no_matching_filter(self, auth_client):
        """Test that GET /v2/operations returns 200 with empty list when no operations match filter."""
        cluster = AWSClusterFactory()

        auth_client.post(
            f"/v1/clusters/{cluster.id}/operations",
            json={"type": "deploy", "status": "completed", "cicd_url": "https://example.com/1"},
        )

        response = auth_client.get("/v2/operations?type=nonexistent")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_operations_v2_unauthorized(self, unauth_client):
        """Test that GET /v2/operations without credentials returns 401."""
        response = unauth_client.get("/v2/operations")
        assert response.status_code == 401
