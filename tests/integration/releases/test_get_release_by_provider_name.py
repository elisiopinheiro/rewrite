import pytest
from factories.release_factory import ReleaseFactory

from api.shared.models.clusters import Provider


@pytest.mark.integration
@pytest.mark.clusters4wm_app
@pytest.mark.releases
class TestGetReleaseByProviderName:
    """Integration tests for GET /v1/releases/{provider}/{name} endpoint."""

    def test_get_release_by_provider_name_aws(self, auth_client):
        """Test that GET /v1/releases/{provider}/{name} returns AWS release details."""
        release = ReleaseFactory(name="test-aws-release", provider=Provider.AWS)

        response = auth_client.get(f"/v1/releases/{release.provider}/{release.name}")
        assert response.status_code == 200

        response_data = response.json()
        assert isinstance(response_data, dict)
        assert response_data["id"] == release.id
        assert response_data["name"] == release.name
        assert response_data["provider"] == release.provider
        assert response_data["reserved_namespaces"] == release.reserved_namespaces

    def test_get_release_by_provider_name_azure(self, auth_client):
        """Test that GET /v1/releases/{provider}/{name} returns Azure release details."""
        release = ReleaseFactory(name="test-azure-release", provider=Provider.AZURE)

        response = auth_client.get(f"/v1/releases/{release.provider}/{release.name}")
        assert response.status_code == 200

        response_data = response.json()
        assert isinstance(response_data, dict)
        assert response_data["id"] == release.id
        assert response_data["name"] == release.name
        assert response_data["provider"] == release.provider
        assert response_data["reserved_namespaces"] == release.reserved_namespaces

    def test_get_release_by_provider_name_not_found_name(self, auth_client):
        """Test that non-existent release name returns HTTP 404."""
        ReleaseFactory(name="existing-release", provider=Provider.AWS)

        response = auth_client.get("/v1/releases/aws/non-existent-release")
        assert response.status_code == 404
        assert "Release not found" in response.json()["detail"]

    def test_get_release_by_provider_name_not_found_provider(self, auth_client):
        """Test that release with wrong provider returns HTTP 404."""
        release = ReleaseFactory(name="test-release", provider=Provider.AWS)

        response = auth_client.get(f"/v1/releases/azure/{release.name}")
        assert response.status_code == 404
        assert "Release not found" in response.json()["detail"]
