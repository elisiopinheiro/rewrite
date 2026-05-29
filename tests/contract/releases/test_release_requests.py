import pytest
from contract.releases.schemas.release_request_v1 import ReleaseRequestContractV1
from factories.release_factory import make_add_release_payload, make_release_with_features_payload

from api.shared.models.clusters import Provider


@pytest.mark.contract
@pytest.mark.clusters4wm_app
@pytest.mark.releases
class TestContractReleaseRequests:
    """Contract tests for release request payloads."""

    def test_contract_add_release_aws(self, auth_client):
        """Test that POST /v1/releases AWS request payload matches contract schema."""
        aws_release_data = make_add_release_payload(provider=Provider.AWS)
        ReleaseRequestContractV1(**aws_release_data)
        response = auth_client.post("/v1/releases", json=aws_release_data)
        assert response.status_code == 200

    def test_contract_add_release_azure(self, auth_client):
        """Test that POST /v1/releases Azure request payload matches contract schema."""
        azure_release_data = make_add_release_payload(provider=Provider.AZURE)
        ReleaseRequestContractV1(**azure_release_data)
        response = auth_client.post("/v1/releases", json=azure_release_data)
        assert response.status_code == 200

    def test_contract_add_release_with_features(self, auth_client):
        """Test that POST /v1/releases request with features matches contract schema."""
        # Test AWS release with features request validation
        aws_release_data = make_release_with_features_payload(provider=Provider.AWS)
        ReleaseRequestContractV1(**aws_release_data)
        response = auth_client.post("/v1/releases", json=aws_release_data)
        assert response.status_code == 200

        # Test Azure release with features request validation
        azure_release_data = make_release_with_features_payload(provider=Provider.AZURE)
        ReleaseRequestContractV1(**azure_release_data)
        response = auth_client.post("/v1/releases", json=azure_release_data)
        assert response.status_code == 200
