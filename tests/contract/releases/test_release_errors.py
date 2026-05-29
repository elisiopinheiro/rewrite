import pytest
from factories.release_factory import ReleaseFactory, make_add_release_payload

from api.shared.models.clusters import Provider


@pytest.mark.contract
@pytest.mark.clusters4wm_app
@pytest.mark.releases
class TestContractReleaseErrors:
    """Contract tests for release error responses."""

    @pytest.mark.conflict
    class TestConflict:
        """Tests for HTTP 409 conflict responses."""

        def test_add_release_duplicate_name_provider(self, auth_client, db_session):
            """Test that creating a release with duplicate name and provider returns HTTP 409."""
            ReleaseFactory(name="duplicate-release", provider=Provider.AWS)

            # Try to create a release with the same name and provider via API
            release_data = make_add_release_payload(provider=Provider.AWS, name="duplicate-release")
            response = auth_client.post("/v1/releases", json=release_data)
            assert response.status_code == 409
            assert "already exists" in response.json()["detail"]

    @pytest.mark.not_found
    class TestNotFound:
        """Tests for HTTP 404 not found responses."""

        def test_get_release_not_found(self, auth_client):
            """Test that GET /v1/releases/{provider}/{name} returns HTTP 404 for non-existent release."""
            response = auth_client.get("/v1/releases/aws/non-existent-release")
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

        def test_delete_release_not_found(self, auth_client):
            """Test that DELETE /v1/releases/{id} returns HTTP 404 for non-existent release."""
            response = auth_client.delete("/v1/releases/999999")
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    @pytest.mark.validation
    class TestValidationErrors:
        """Tests for HTTP 422 validation error responses."""

        @pytest.mark.parametrize(
            "invalid_data",
            [
                # Missing required fields
                {"provider": "aws"},  # missing name
                {"name": "test-release"},  # missing provider
                # Invalid provider
                {"name": "test-release", "provider": "invalid-provider"},
                # Invalid data types
                {"name": "test-release", "provider": "aws", "reserved_namespaces": "not-a-list"},  # should be list
            ],
        )
        def test_add_release_invalid_request(self, auth_client, invalid_data):
            """Test that invalid request payloads return HTTP 422."""
            response = auth_client.post("/v1/releases", json=invalid_data)
            assert response.status_code == 422
