import pytest
from factories.release_factory import ReleaseFactory

from api.shared.models.clusters import Provider


@pytest.mark.integration
@pytest.mark.clusters4wm_app
@pytest.mark.releases
class TestGetReleases:
    """Integration tests for GET /v1/releases endpoint."""

    def test_get_releases_all(self, auth_client):
        """Test that GET /v1/releases returns all releases."""
        ReleaseFactory(name="test-aws-release", provider=Provider.AWS)
        ReleaseFactory(name="test-azure-release", provider=Provider.AZURE)

        response = auth_client.get("/v1/releases")
        assert response.status_code == 200

        response_data = response.json()
        assert isinstance(response_data, list)
        assert len(response_data) == 2

    def test_get_releases_filter_by_name(self, auth_client):
        """Test that releases can be filtered by name."""
        target_release = ReleaseFactory(name="specific-release-name", provider=Provider.AWS)
        ReleaseFactory(name="release-name", provider=Provider.AZURE)

        response = auth_client.get(f"/v1/releases?name={target_release.name}")
        assert response.status_code == 200

        response_data = response.json()
        assert isinstance(response_data, list)
        assert len(response_data) == 1

    def test_get_releases_filter_by_provider(self, auth_client):
        """Test that releases can be filtered by provider."""
        ReleaseFactory(name="aws-release-1", provider=Provider.AWS)
        ReleaseFactory(name="aws-release-2", provider=Provider.AWS)
        ReleaseFactory(name="azure-release-1", provider=Provider.AZURE)

        response = auth_client.get("/v1/releases?provider=aws")
        assert response.status_code == 200

        response_data = response.json()
        assert isinstance(response_data, list)
        assert len(response_data) == 2

        # Check that all returned releases are AWS
        for release in response_data:
            assert release["provider"] == Provider.AWS.value

    def test_get_releases_order_by_name(self, auth_client):
        """Test that releases can be ordered by name."""
        ReleaseFactory(name="aws-release1", provider=Provider.AWS)
        ReleaseFactory(name="aws-release2", provider=Provider.AWS)
        ReleaseFactory(name="aws-release3", provider=Provider.AWS)

        response = auth_client.get("/v1/releases?order_by=name")
        assert response.status_code == 200

        response_data = response.json()
        assert isinstance(response_data, list)
        assert len(response_data) == 3

        # Check that releases are ordered by name
        release_names = [release["name"] for release in response_data]
        assert release_names == sorted(release_names)

    def test_get_releases_no_releases_with_filter(self, auth_client):
        """Test that non-matching filter returns 404."""
        ReleaseFactory(name="existing-release", provider=Provider.AWS)

        # Search for non-existent release
        response = auth_client.get("/v1/releases?name=non-existent-release")
        assert response.status_code == 404
        assert response.json()["detail"] == "No releases found"

    def test_get_releases_empty_database(self, auth_client):
        """Test that empty database returns 404."""
        response = auth_client.get("/v1/releases")
        assert response.status_code == 404
        assert response.json()["detail"] == "No releases found"

    def test_get_releases_invalid_order_by_returns_422(self, auth_client):
        """Test that an invalid order_by value returns 422."""
        response = auth_client.get("/v1/releases?order_by=nonexistent_column")
        assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.clusters4wm_app
@pytest.mark.releases
class TestGetRelease:
    """Tests for GET /v1/releases/{provider}/{name}"""

    @pytest.mark.parametrize(
        "release_name, provider",
        [
            ("release/1.0.0", Provider.AWS.value),
            ("release/test", Provider.AZURE.value),
            ("feature/something", Provider.AWS.value),
            ("fix/something", Provider.AZURE.value),
            ("1.0.0", Provider.AWS.value),
            ("development", Provider.AZURE.value),
        ],
    )
    def test_get_release(self, auth_client, db_session, release_name, provider):
        """Tests that retrieving tag-based or branch-based releases work properly"""

        ReleaseFactory(name=release_name, provider=provider)
        response = auth_client.get(f"/v1/releases/{provider}/{release_name}")
        assert response.status_code == 200
        assert response.json()["name"] == release_name
