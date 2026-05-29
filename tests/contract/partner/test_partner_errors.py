"""Contract tests for Partner API related endpoints"""

import pytest
from conftest import CF_CREDENTIALS, M4W_CREDENTIALS, SCP_CREDENTIALS, SOLAR_CREDENTIALS
from factories.cluster_factory import AWSClusterFactory, AzureClusterFactory

NOT_FOUND_MSG = "No clusters found"
UNAUTHORIZED_MSG = "You do not have the necessary permissions to access this resource."
NOT_AUTHENTICATED_MSG = "Not authenticated"


@pytest.mark.contract
@pytest.mark.partner_app
class TestContractPartnerErrors:
    """Contract tests for partner API error responses."""

    @pytest.mark.not_found
    class TestNotFound:
        """Tests for HTTP 404 not found responses."""

        @pytest.mark.scp
        @pytest.mark.cf
        class TestSCPNotFound:
            """Tests for SCP endpoint not found scenarios."""

            @pytest.mark.parametrize(
                "auth_partner_client",
                [
                    (M4W_CREDENTIALS),
                    (SCP_CREDENTIALS),
                    (CF_CREDENTIALS),
                ],
                indirect=["auth_partner_client"],
            )
            def test_contract_scp_get_clusters_without_any_clusters(self, auth_partner_client):
                """Test that GET /v1/clusters returns HTTP 404 when no clusters exist."""
                response = auth_partner_client.get("/v1/clusters")
                assert response.status_code == 404
                assert response.json().get("message") == NOT_FOUND_MSG

            @pytest.mark.parametrize(
                "auth_partner_client",
                [
                    (M4W_CREDENTIALS),
                    (SCP_CREDENTIALS),
                    (CF_CREDENTIALS),
                ],
                indirect=["auth_partner_client"],
            )
            def test_contract_scp_get_aws_cluster(self, auth_partner_client):
                """Test that GET /v1/clusters returns HTTP 404 for AWS clusters."""
                cluster_name = "4wm-cluster-dev"
                AWSClusterFactory(name=cluster_name)
                response = auth_partner_client.get("/v1/clusters", params={"name": cluster_name})
                assert response.status_code == 404
                assert response.json().get("message") == NOT_FOUND_MSG

            @pytest.mark.parametrize(
                "auth_partner_client",
                [
                    (M4W_CREDENTIALS),
                    (SCP_CREDENTIALS),
                    (CF_CREDENTIALS),
                ],
                indirect=["auth_partner_client"],
            )
            def test_contract_scp_get_non_existent_cluster(self, auth_partner_client):
                """Test that GET /v1/clusters returns HTTP 404 for non-existent cluster name."""
                cluster_name = "4wm-cluster-dev"
                AzureClusterFactory(name=cluster_name)
                response = auth_partner_client.get("/v1/clusters", params={"name": f"_{cluster_name}"})
                assert response.status_code == 404
                assert response.json().get("message") == NOT_FOUND_MSG

        @pytest.mark.solar
        class TestSOLARNotFound:
            """Tests for SOLAR endpoint not found scenarios."""

            @pytest.mark.parametrize(
                "auth_partner_client",
                [
                    (M4W_CREDENTIALS),
                    (SOLAR_CREDENTIALS),
                ],
                indirect=["auth_partner_client"],
            )
            def test_contract_solar_get_clusters_without_any_clusters(self, auth_partner_client):
                """Test that GET /v1/solar/clusters returns HTTP 404 when no clusters exist."""
                response = auth_partner_client.get("/v1/solar/clusters")
                assert response.status_code == 404
                assert response.json().get("message") == NOT_FOUND_MSG

            @pytest.mark.parametrize(
                "auth_partner_client",
                [
                    (M4W_CREDENTIALS),
                    (SOLAR_CREDENTIALS),
                ],
                indirect=["auth_partner_client"],
            )
            def test_contract_solar_get_non_existent_cluster(self, auth_partner_client):
                """Test that GET /v1/solar/clusters returns HTTP 404 for non-existent cluster name."""
                cluster_name = "4wm-cluster-dev"
                AWSClusterFactory(name=f"{cluster_name}-aws")
                response = auth_partner_client.get("/v1/solar/clusters", params={"name": cluster_name})
                assert response.status_code == 404
                assert response.json().get("message") == NOT_FOUND_MSG
                AzureClusterFactory(name=f"{cluster_name}-azure")
                response = auth_partner_client.get("/v1/solar/clusters", params={"name": cluster_name})
                assert response.status_code == 404
                assert response.json().get("message") == NOT_FOUND_MSG

    @pytest.mark.authorization
    class TestUnauthorized:
        """Tests for HTTP 403 forbidden responses."""

        @pytest.mark.scp
        @pytest.mark.cf
        class TestSCPUnauthorized:
            """Tests for SCP endpoint unauthorized access."""

            @pytest.mark.parametrize(
                "auth_partner_client",
                [
                    (SOLAR_CREDENTIALS),
                ],
                indirect=["auth_partner_client"],
            )
            def test_contract_scp_get_clusters_without_any_clusters_unauthorized(self, auth_partner_client):
                """Test that SOLAR credentials cannot access SCP endpoint."""
                response = auth_partner_client.get("/v1/clusters")
                assert response.status_code == 403
                assert response.json().get("detail") == UNAUTHORIZED_MSG

            @pytest.mark.parametrize(
                "auth_partner_client",
                [
                    (SOLAR_CREDENTIALS),
                ],
                indirect=["auth_partner_client"],
            )
            def test_contract_scp_get_non_existent_cluster_unauthorized(self, auth_partner_client):
                """Test that SOLAR credentials cannot access SCP endpoint with filters."""
                response = auth_partner_client.get("/v1/clusters", params={"name": "4wm-cluster-dev"})
                assert response.status_code == 403
                assert response.json().get("detail") == UNAUTHORIZED_MSG

        @pytest.mark.solar
        class TestSOLARUnauthorized:
            """Tests for SOLAR endpoint unauthorized access."""

            @pytest.mark.parametrize(
                "auth_partner_client",
                [
                    (SCP_CREDENTIALS),
                    (CF_CREDENTIALS),
                ],
                indirect=["auth_partner_client"],
            )
            def test_contract_solar_get_clusters_without_any_clusters_unauthorized(self, auth_partner_client):
                """Test that SCP/CF credentials cannot access SOLAR endpoint."""
                response = auth_partner_client.get("/v1/solar/clusters")
                assert response.status_code == 403
                assert response.json().get("detail") == UNAUTHORIZED_MSG

            @pytest.mark.parametrize(
                "auth_partner_client",
                [
                    (SCP_CREDENTIALS),
                    (CF_CREDENTIALS),
                ],
                indirect=["auth_partner_client"],
            )
            def test_contract_solar_get_non_existent_cluster_unauthorized(self, auth_partner_client):
                """Test that SCP/CF credentials cannot access SOLAR endpoint with filters."""
                response = auth_partner_client.get("/v1/solar/clusters", params={"name": "4wm-cluster-dev"})
                assert response.status_code == 403
                assert response.json().get("detail") == UNAUTHORIZED_MSG

    class TestUnauthenticated:
        """Tests for HTTP 401 unauthenticated responses."""

        @pytest.mark.scp
        @pytest.mark.cf
        class TestSCPUnauthenticated:
            """Tests for SCP endpoint unauthenticated access."""

            def test_contract_scp_get_clusters_without_any_clusters_unauthenticated(self, unauth_partner_client):
                """Test that unauthenticated requests to SCP endpoint return HTTP 401."""
                response = unauth_partner_client.get("/v1/clusters")
                assert response.status_code == 401
                assert response.json().get("detail") == NOT_AUTHENTICATED_MSG

            def test_contract_scp_get_non_existent_cluster_unauthenticated(self, unauth_partner_client):
                """Test that unauthenticated requests to SCP endpoint with filters return HTTP 401."""
                response = unauth_partner_client.get("/v1/clusters", params={"name": "4wm-cluster-dev"})
                assert response.status_code == 401
                assert response.json().get("detail") == NOT_AUTHENTICATED_MSG

        @pytest.mark.solar
        class TestSOLARUnauthenticated:
            """Tests for SOLAR endpoint unauthenticated access."""

            def test_contract_solar_get_clusters_without_any_clusters_unauthenticated(self, unauth_partner_client):
                """Test that unauthenticated requests to SOLAR endpoint return HTTP 401."""
                response = unauth_partner_client.get("/v1/solar/clusters")
                assert response.status_code == 401
                assert response.json().get("detail") == NOT_AUTHENTICATED_MSG

            def test_contract_solar_get_non_existent_cluster_unauthenticated(self, unauth_partner_client):
                """Test that unauthenticated requests to SOLAR endpoint with filters return HTTP 401."""
                response = unauth_partner_client.get("/v1/solar/clusters", params={"name": "4wm-cluster-dev"})
                assert response.status_code == 401
                assert response.json().get("detail") == NOT_AUTHENTICATED_MSG
