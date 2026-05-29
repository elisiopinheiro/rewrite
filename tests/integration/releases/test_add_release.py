import pytest
from factories.release_factory import make_add_release_payload, make_release_with_features_payload
from utils import popper

from api.shared.models.clusters import Provider


@pytest.mark.integration
@pytest.mark.clusters4wm_app
@pytest.mark.releases
class TestAddRelease:
    """Integration tests for POST /v1/releases endpoint."""

    def test_add_release_aws(self, auth_client):
        """Test that POST /v1/releases creates an AWS release."""
        release_data = make_add_release_payload(provider=Provider.AWS)
        response = auth_client.post("/v1/releases", json=release_data)
        response_data = response.json()
        popper(response_data, ["id"])
        assert response.status_code == 200
        assert isinstance(response_data, dict)
        assert response_data["name"] == release_data["name"]
        assert response_data["provider"] == release_data["provider"]
        assert response_data["reserved_namespaces"] == release_data["reserved_namespaces"]

    def test_add_release_azure(self, auth_client):
        """Test that POST /v1/releases creates an Azure release."""
        release_data = make_add_release_payload(provider=Provider.AZURE)
        response = auth_client.post("/v1/releases", json=release_data)
        response_data = response.json()
        popper(response_data, ["id"])
        assert response.status_code == 200
        assert isinstance(response_data, dict)
        assert response_data["name"] == release_data["name"]
        assert response_data["provider"] == release_data["provider"]
        assert response_data["reserved_namespaces"] == release_data["reserved_namespaces"]

    @pytest.mark.optional_features
    class TestFeatures:
        """Tests for release features."""

        def test_add_release_with_features(self, auth_client):
            """Test that release accepts features."""
            release_data = make_release_with_features_payload(provider=Provider.AWS)
            response = auth_client.post("/v1/releases", json=release_data)
            response_data = response.json()

            assert response.status_code == 200
            assert isinstance(response_data, dict)
            assert response_data["name"] == release_data["name"]
            assert response_data["provider"] == release_data["provider"]
            assert response_data["reserved_namespaces"] == release_data["reserved_namespaces"]
            assert "features" in response_data
            assert len(response_data["features"]) == len(release_data["features"])

        def test_add_release_without_features(self, auth_client):
            """Test that features field defaults to empty when not provided."""
            release_data = make_add_release_payload(provider=Provider.AWS)
            # Remove features field
            release_data.pop("features")

            response = auth_client.post("/v1/releases", json=release_data)
            assert response.status_code == 200
            response_data = response.json()
            assert "features" in response_data
            assert response_data["features"] == []

    @pytest.mark.reserved_namespaces
    class TestReservedNamespaces:
        """Tests for reserved namespaces."""

        def test_add_release_without_reserved_namespaces(self, auth_client):
            """Test that reserved_namespaces field defaults to empty when not provided."""
            release_data = make_add_release_payload(provider=Provider.AWS)
            # Remove reserved_namespaces field
            release_data.pop("reserved_namespaces")

            response = auth_client.post("/v1/releases", json=release_data)
            assert response.status_code == 200
            response_data = response.json()
            assert "reserved_namespaces" in response_data
            assert response_data["reserved_namespaces"] == []

        def test_add_release_with_empty_reserved_namespaces(self, auth_client):
            """Test that empty reserved_namespaces is accepted."""
            release_data = make_add_release_payload(provider=Provider.AWS)
            release_data["reserved_namespaces"] = []

            response = auth_client.post("/v1/releases", json=release_data)
            assert response.status_code == 200
            response_data = response.json()
            assert "reserved_namespaces" in response_data
            assert response_data["reserved_namespaces"] == []

    def test_add_release_invalid_payload(self, auth_client):
        """Test that POST /v1/releases with invalid payload returns 422."""
        response = auth_client.post("/v1/releases", json={"invalid_field": "value"})
        assert response.status_code == 422

    def test_add_release_unauthorized(self, unauth_client):
        """Test that POST /v1/releases without credentials returns 401."""
        release_data = make_add_release_payload(provider=Provider.AWS)
        response = unauth_client.post("/v1/releases", json=release_data)
        assert response.status_code == 401
