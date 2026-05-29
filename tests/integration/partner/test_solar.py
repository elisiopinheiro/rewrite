"""Integration tests for SOLAR related endpoints"""

import pytest
from conftest import CF_CREDENTIALS, M4W_CREDENTIALS, SCP_CREDENTIALS, SOLAR_CREDENTIALS
from factories.cluster_factory import AWSClusterFactory, AzureClusterFactory


@pytest.mark.integration
@pytest.mark.partner_app
@pytest.mark.solar
class TestSolarListResponses:
    """Integration tests for SOLAR partner GET /v1/solar/clusters endpoint."""

    @pytest.mark.parametrize(
        "auth_partner_client, azure_clusters_count, aws_clusters_count",
        [
            (M4W_CREDENTIALS, 1, 1),
            (SOLAR_CREDENTIALS, 1, 1),
            (M4W_CREDENTIALS, 2, 2),
            (SOLAR_CREDENTIALS, 2, 2),
            (M4W_CREDENTIALS, 10, 10),
            (SOLAR_CREDENTIALS, 10, 10),
        ],
        indirect=["auth_partner_client"],
    )
    def test_solar_list_clusters(self, auth_partner_client, azure_clusters_count, aws_clusters_count):
        """Test that GET /v1/solar/clusters returns both AWS and Azure clusters."""
        [AzureClusterFactory() for _ in range(azure_clusters_count)]
        [AWSClusterFactory() for _ in range(aws_clusters_count)]
        response = auth_partner_client.get("/v1/solar/clusters")
        assert response.status_code == 200
        assert response.json().get("count") == azure_clusters_count + aws_clusters_count

    @pytest.mark.parametrize(
        "auth_partner_client, azure_clusters_count, aws_clusters_count",
        [
            (M4W_CREDENTIALS, 1, 1),
            (SOLAR_CREDENTIALS, 1, 1),
            (M4W_CREDENTIALS, 2, 2),
            (SOLAR_CREDENTIALS, 2, 2),
            (M4W_CREDENTIALS, 10, 10),
            (SOLAR_CREDENTIALS, 10, 10),
        ],
        indirect=["auth_partner_client"],
    )
    def test_solar_list_clusters_with_filters(self, auth_partner_client, azure_clusters_count, aws_clusters_count):
        """Test that clusters can be filtered by provider."""
        [AzureClusterFactory() for _ in range(azure_clusters_count)]
        [AWSClusterFactory() for _ in range(aws_clusters_count)]
        response = auth_partner_client.get("/v1/solar/clusters", params={"provider": "aws"})
        assert response.status_code == 200
        assert response.json().get("count") == aws_clusters_count

    @pytest.mark.parametrize(
        "auth_partner_client", [(M4W_CREDENTIALS), (SOLAR_CREDENTIALS)], indirect=["auth_partner_client"]
    )
    def test_solar_list_clusters_no_clusters(self, auth_partner_client):
        """Test that empty database returns HTTP 404."""
        response = auth_partner_client.get("/v1/solar/clusters")
        assert response.status_code == 404
        assert response.json().get("message") == "No clusters found"

    @pytest.mark.parametrize(
        "auth_partner_client", [(SCP_CREDENTIALS), (CF_CREDENTIALS)], indirect=["auth_partner_client"]
    )
    def test_solar_list_clusters_unauthorized_client(self, auth_partner_client):
        """Test that SCP/CF credentials cannot access SOLAR endpoint."""
        AWSClusterFactory()
        response = auth_partner_client.get("/v1/solar/clusters")
        assert response.status_code == 403
        assert response.json().get("detail") == "You do not have the necessary permissions to access this resource."

    @pytest.mark.parametrize("auth_partner_client", [("123:123")], indirect=["auth_partner_client"])
    def test_solar_list_clusters_incorrect_user(self, auth_partner_client):
        """Test that incorrect credentials return HTTP 401."""
        response = auth_partner_client.get("/v1/solar/clusters")
        assert response.status_code == 401
        assert response.json().get("detail") == "Incorrect username or password"

    def test_solar_list_clusters_no_authenticated_user(self, unauth_partner_client):
        """Test that unauthenticated requests return HTTP 401."""
        response = unauth_partner_client.get("/v1/solar/clusters")
        assert response.status_code == 401
        assert response.json().get("detail") == "Not authenticated"
