import pytest
from factories.cluster_factory import AWSClusterFactory, AzureClusterFactory

from api.shared.models.clusters import Environment


@pytest.mark.integration
@pytest.mark.clusters4wm_app
@pytest.mark.releases
class TestGetClustersInfraRevisions:
    """Integration tests for GET /v1/clusters/infra-revisions endpoint."""

    def test_get_clusters_infra_revisions(self, auth_client):
        """Test that GET /v1/clusters/infra-revisions returns revisions grouped by environment."""
        AWSClusterFactory(infra_revision="1.0.0", environment=Environment.INT, internal=False)
        AzureClusterFactory(infra_revision="2.0.0", environment=Environment.PROD, internal=False)

        response = auth_client.get("/v1/clusters/infra-revisions")
        assert response.status_code == 200

        response_data = response.json()
        assert isinstance(response_data, list)
        assert len(response_data) == 2

    def test_get_clusters_infra_revisions_filter_by_environment(self, auth_client):
        """Test that clusters/infra-revisions can be filtered by environment."""
        AWSClusterFactory(infra_revision="1.0.0", environment=Environment.INT, internal=False)
        AzureClusterFactory(infra_revision="2.0.0", environment=Environment.PROD, internal=False)

        response = auth_client.get("/v1/clusters/infra-revisions?environment=integration")
        assert response.status_code == 200

        response_data = response.json()
        assert isinstance(response_data, list)
        assert len(response_data) == 1

    def test_get_clusters_infra_revisions_empty_database(self, auth_client):
        """Test that empty database returns 404."""
        response = auth_client.get("/v1/clusters/infra-revisions")
        assert response.status_code == 404
        assert response.json()["detail"] == "No revisions found"

    def test_get_clusters_infra_revisions_unauthorized(self, unauth_client):
        """Test that GET /v1/clusters/infra-revisions without credentials returns 401."""
        response = unauth_client.get("/v1/clusters/infra-revisions")
        assert response.status_code == 401
