"""Integration tests for SCP related endpoints"""

import pytest
from conftest import CF_CREDENTIALS, M4W_CREDENTIALS, SCP_CREDENTIALS, SOLAR_CREDENTIALS
from factories.cluster_factory import AWSClusterFactory, AzureClusterFactory


def create_azure_cluster(cluster_name: str = None):
    """Creates an Azure cluster non internal."""
    if cluster_name:
        return AzureClusterFactory(name=cluster_name, internal=False)
    return AzureClusterFactory(internal=False)


def create_aws_cluster():
    """Creates an AWS cluster non internal."""
    return AWSClusterFactory(internal=False)


@pytest.mark.integration
@pytest.mark.partner_app
@pytest.mark.scp
@pytest.mark.cf
class TestSCPListClusters:
    """Integration tests for SCP partner GET /v1/clusters endpoint."""

    @pytest.mark.parametrize(
        "auth_partner_client, azure_clusters_count, aws_clusters_count",
        [
            (M4W_CREDENTIALS, 1, 2),
            (SCP_CREDENTIALS, 1, 2),
            (CF_CREDENTIALS, 1, 2),
            (M4W_CREDENTIALS, 2, 12),
            (SCP_CREDENTIALS, 2, 12),
            (CF_CREDENTIALS, 2, 12),
            (M4W_CREDENTIALS, 10, 1),
            (SCP_CREDENTIALS, 10, 1),
            (CF_CREDENTIALS, 10, 1),
        ],
        indirect=["auth_partner_client"],
    )
    def test_scp_list_clusters(self, auth_partner_client, azure_clusters_count, aws_clusters_count):
        """Test that GET /v1/clusters returns only Azure clusters."""
        [create_azure_cluster() for _ in range(azure_clusters_count)]
        [create_aws_cluster() for _ in range(aws_clusters_count)]
        response = auth_partner_client.get("/v1/clusters")
        assert response.status_code == 200
        assert response.json().get("count") == azure_clusters_count

    @pytest.mark.parametrize(
        "auth_partner_client, azure_clusters_count, aws_clusters_count",
        [
            (M4W_CREDENTIALS, 10, 1),
            (SCP_CREDENTIALS, 10, 1),
            (CF_CREDENTIALS, 10, 1),
        ],
        indirect=["auth_partner_client"],
    )
    def test_scp_list_clusters_with_filters(self, auth_partner_client, azure_clusters_count, aws_clusters_count):
        """Test that clusters can be filtered by name."""
        cluster_name = "4wm-cluster-dev"
        create_azure_cluster(cluster_name=cluster_name)
        [create_azure_cluster() for _ in range(azure_clusters_count)]
        [create_aws_cluster() for _ in range(aws_clusters_count)]
        response = auth_partner_client.get("/v1/clusters", params={"name": cluster_name})
        assert response.status_code == 200
        assert response.json().get("count") == 1
        assert all(cluster.get("name") == cluster_name for cluster in response.json().get("clusters", []))

    @pytest.mark.parametrize(
        "auth_partner_client, aws_clusters_count",
        [
            (M4W_CREDENTIALS, 0),
            (M4W_CREDENTIALS, 3),
            (SCP_CREDENTIALS, 0),
            (SCP_CREDENTIALS, 3),
            (CF_CREDENTIALS, 0),
            (CF_CREDENTIALS, 3),
        ],
        indirect=["auth_partner_client"],
    )
    def test_scp_list_clusters_no_azure_clusters(self, auth_partner_client, aws_clusters_count):
        """Test that only AWS clusters returns HTTP 404."""
        [AWSClusterFactory() for _ in range(aws_clusters_count)]
        response = auth_partner_client.get("/v1/clusters")
        assert response.status_code == 404
        assert response.json().get("message") == "No clusters found"

    @pytest.mark.parametrize("auth_partner_client", [(SOLAR_CREDENTIALS)], indirect=["auth_partner_client"])
    def test_scp_list_clusters_unauthorized_client(self, auth_partner_client):
        """Test that SOLAR credentials cannot access SCP endpoint."""
        response = auth_partner_client.get("/v1/clusters")
        assert response.status_code == 403
        assert response.json().get("detail") == "You do not have the necessary permissions to access this resource."

    @pytest.mark.parametrize("auth_partner_client", [("123:123")], indirect=["auth_partner_client"])
    def test_scp_list_clusters_incorrect_user(self, auth_partner_client):
        """Test that incorrect credentials return HTTP 401."""
        response = auth_partner_client.get("/v1/clusters")
        assert response.status_code == 401
        assert response.json().get("detail") == "Incorrect username or password"

    def test_scp_list_clusters_no_authenticated_user(self, unauth_partner_client):
        """Test that unauthenticated requests return HTTP 401."""
        response = unauth_partner_client.get("/v1/clusters")
        assert response.status_code == 401
        assert response.json().get("detail") == "Not authenticated"
