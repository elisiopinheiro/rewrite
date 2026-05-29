import pytest
from factories.cluster_factory import AWSClusterFactory, AzureClusterFactory

from api.shared.models.clusters import Environment


@pytest.mark.integration
@pytest.mark.clusters4wm_app
@pytest.mark.releases
class TestGetClustersReleases:
    """Integration tests for GET /v1/clusters/releases endpoint."""

    def test_get_clusters_releases(self, auth_client):
        """Test that GET /v1/clusters/releases returns releases grouped by environment."""
        AWSClusterFactory(release="1.0.0", environment=Environment.INT, internal=False)
        AzureClusterFactory(release="2.0.0", environment=Environment.PROD, internal=False)

        response = auth_client.get("/v1/clusters/releases")
        assert response.status_code == 200

        response_data = response.json()
        assert isinstance(response_data, list)
        assert len(response_data) == 2

    def test_get_clusters_releases_filter_by_environment(self, auth_client):
        """Test that clusters/releases can be filtered by environment."""
        AWSClusterFactory(release="1.0.0", environment=Environment.INT, internal=False)
        AzureClusterFactory(release="2.0.0", environment=Environment.PROD, internal=False)

        response = auth_client.get("/v1/clusters/releases?environment=integration")
        assert response.status_code == 200

        response_data = response.json()
        assert isinstance(response_data, list)
        assert len(response_data) == 1

    def test_get_clusters_releases_empty_database(self, auth_client):
        """Test that empty database returns 404."""
        response = auth_client.get("/v1/clusters/releases")
        assert response.status_code == 404
        assert response.json()["detail"] == "No releases found"

    def test_get_clusters_releases_unauthorized(self, unauth_client):
        """Test that GET /v1/clusters/releases without credentials returns 401."""
        response = unauth_client.get("/v1/clusters/releases")
        assert response.status_code == 401
