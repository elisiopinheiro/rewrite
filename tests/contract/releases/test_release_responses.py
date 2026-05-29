import pytest
from contract.releases.schemas.release_response_v1 import ReleaseResponseContractV1
from factories.release_factory import ReleaseFactory

from api.shared.models.clusters import Provider


@pytest.mark.contract
@pytest.mark.clusters4wm_app
@pytest.mark.releases
class TestContractReleaseResponses:
    """Contract tests for release response payloads."""

    def test_contract_release_response(self, auth_client):
        """Test that GET /v1/releases response with filter matches contract schema."""
        release = ReleaseFactory()

        response = auth_client.get(f"/v1/releases?id={release.id}")
        assert response.status_code == 200

        response_data = response.json()
        assert isinstance(response_data, list)

        ReleaseResponseContractV1(**response_data[0])

    def test_contract_get_releases_response(self, auth_client):
        """Test that GET /v1/releases response matches contract schema."""
        ReleaseFactory(name="test-release-1", provider=Provider.AWS)
        ReleaseFactory(name="test-release-2", provider=Provider.AZURE)

        response = auth_client.get("/v1/releases")
        assert response.status_code == 200

        response_data = response.json()
        assert isinstance(response_data, list)

        for release_data in response_data:
            ReleaseResponseContractV1(**release_data)

    def test_contract_get_release_by_provider_response(self, auth_client):
        """Test that GET /v1/releases/{provider}/{name} response matches contract schema."""
        release = ReleaseFactory(name="test-release-specific", provider=Provider.AWS)

        response = auth_client.get(f"/v1/releases/{release.provider}/{release.name}")
        assert response.status_code == 200

        response_data = response.json()
        ReleaseResponseContractV1(**response_data)
