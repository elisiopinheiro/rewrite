import pytest
from factories.release_factory import ReleaseFactory

from api.shared.models.clusters import Provider


@pytest.mark.integration
@pytest.mark.clusters4wm_app
@pytest.mark.releases
class TestGetReleasesV2:
    """Integration tests for GET /v2/releases endpoint."""

    def test_get_releases_v2_all(self, auth_client):
        """Test that GET /v2/releases returns all releases."""
        ReleaseFactory(name="test-aws-release", provider=Provider.AWS)
        ReleaseFactory(name="test-azure-release", provider=Provider.AZURE)

        response = auth_client.get("/v2/releases")
        assert response.status_code == 200

        response_data = response.json()
        assert isinstance(response_data, list)
        assert len(response_data) == 2

    def test_get_releases_v2_filter_by_name(self, auth_client):
        """Test that releases can be filtered by name."""
        target_release = ReleaseFactory(name="specific-release-name", provider=Provider.AWS)
        ReleaseFactory(name="release-name", provider=Provider.AZURE)

        response = auth_client.get(f"/v2/releases?name={target_release.name}")
        assert response.status_code == 200

        response_data = response.json()
        assert isinstance(response_data, list)
        assert len(response_data) == 1

    def test_get_releases_v2_filter_by_provider(self, auth_client):
        """Test that releases can be filtered by provider."""
        ReleaseFactory(name="aws-release-1", provider=Provider.AWS)
        ReleaseFactory(name="aws-release-2", provider=Provider.AWS)
        ReleaseFactory(name="azure-release-1", provider=Provider.AZURE)

        response = auth_client.get("/v2/releases?provider=aws")
        assert response.status_code == 200

        response_data = response.json()
        assert isinstance(response_data, list)
        assert len(response_data) == 2

        for release in response_data:
            assert release["provider"] == Provider.AWS.value

    def test_get_releases_v2_order_by_name(self, auth_client):
        """Test that releases can be ordered by name."""
        ReleaseFactory(name="aws-release1", provider=Provider.AWS)
        ReleaseFactory(name="aws-release2", provider=Provider.AWS)
        ReleaseFactory(name="aws-release3", provider=Provider.AWS)

        response = auth_client.get("/v2/releases?order_by=name")
        assert response.status_code == 200

        response_data = response.json()
        assert isinstance(response_data, list)
        assert len(response_data) == 3

        release_names = [release["name"] for release in response_data]
        assert release_names == sorted(release_names)

    def test_get_releases_v2_no_releases_with_filter(self, auth_client):
        """Test that non-matching filter returns 200 with empty list."""
        ReleaseFactory(name="existing-release", provider=Provider.AWS)

        response = auth_client.get("/v2/releases?name=non-existent-release")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_releases_v2_empty_database(self, auth_client):
        """Test that empty database returns 200 with empty list."""
        response = auth_client.get("/v2/releases")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_releases_v2_invalid_order_by_returns_422(self, auth_client):
        """Test that an invalid order_by value returns 422."""
        response = auth_client.get("/v2/releases?order_by=nonexistent_column")
        assert response.status_code == 422

    def test_get_releases_v2_unauthorized(self, unauth_client):
        """Test that GET /v2/releases without credentials returns 401."""
        response = unauth_client.get("/v2/releases")
        assert response.status_code == 401
