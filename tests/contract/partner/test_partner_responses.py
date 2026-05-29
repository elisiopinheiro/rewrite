"""Contract tests for Partner API related endpoints"""

from random import randint

import pytest
from conftest import CF_CREDENTIALS, M4W_CREDENTIALS, SCP_CREDENTIALS, SOLAR_CREDENTIALS
from contract.partner.schemas.scp_clusters_response import SCPClusterResponseContract
from contract.partner.schemas.solar_clusters_reponse import SOLARClusterResponseContract
from factories.cluster_factory import AWSClusterFactory, AzureClusterFactory


def create_azure_cluster(name: str = None, internal: bool = False):
    """Creates an Azure cluster non internal."""
    if name:
        return AzureClusterFactory(name=name, internal=internal)
    return AzureClusterFactory(internal=internal)


def create_aws_cluster(internal: bool = False):
    """Creates an AWS cluster non internal."""
    return AWSClusterFactory(internal=internal)


@pytest.mark.contract
@pytest.mark.partner_app
class TestContractPartnerResponses:
    """Contract tests for partner API response payloads."""

    @pytest.mark.scp
    @pytest.mark.cf
    class TestScpResponses:
        """Tests for SCP endpoint response contracts."""

        @pytest.mark.parametrize(
            "auth_partner_client",
            [
                (M4W_CREDENTIALS),
                (SCP_CREDENTIALS),
                (CF_CREDENTIALS),
            ],
            indirect=["auth_partner_client"],
        )
        def test_contract_scp_list_clusters(self, auth_partner_client):
            """Test that GET /v1/clusters response matches SCP contract schema."""
            cluster_count = 10
            [create_azure_cluster() for _ in range(cluster_count)]
            [create_aws_cluster() for _ in range(cluster_count)]
            [create_azure_cluster(internal=True) for _ in range(randint(1, 10))]
            [create_aws_cluster(internal=True) for _ in range(randint(1, 10))]
            response = auth_partner_client.get("/v1/clusters")
            assert response.status_code == 200
            # AWS clusters are not listed in SCP endpoint
            assert len(response.json().get("clusters", [])) == cluster_count
            SCPClusterResponseContract(**response.json())

        @pytest.mark.parametrize(
            "auth_partner_client",
            [
                (M4W_CREDENTIALS),
                (SCP_CREDENTIALS),
                (CF_CREDENTIALS),
            ],
            indirect=["auth_partner_client"],
        )
        def test_contract_scp_get_cluster_by_name(self, auth_partner_client):
            """Test that filtered GET /v1/clusters response matches SCP contract schema."""
            clusters_count = 10
            [create_azure_cluster() for _ in range(clusters_count)]
            [create_aws_cluster() for _ in range(clusters_count)]
            [create_azure_cluster(internal=True) for _ in range(randint(1, 10))]
            [create_aws_cluster(internal=True) for _ in range(randint(1, 10))]
            azure_cluster_name = "4wm-cluster-dev-azure"
            create_azure_cluster(name=azure_cluster_name)
            response = auth_partner_client.get("/v1/clusters", params={"name": azure_cluster_name})
            assert response.status_code == 200
            assert len(response.json().get("clusters", [])) == 1
            SCPClusterResponseContract(**response.json())

    @pytest.mark.solar
    class TestSolarResponses:
        """Tests for SOLAR endpoint response contracts."""

        @pytest.mark.parametrize(
            "auth_partner_client",
            [
                (M4W_CREDENTIALS),
                (SOLAR_CREDENTIALS),
            ],
            indirect=["auth_partner_client"],
        )
        def test_contract_solar_list_clusters_without_filters(self, auth_partner_client):
            """Test that GET /v1/solar/clusters response matches SOLAR contract schema."""
            clusters_count = 10
            [AzureClusterFactory() for _ in range(clusters_count)]
            [AWSClusterFactory() for _ in range(clusters_count)]
            response = auth_partner_client.get("/v1/solar/clusters")
            assert response.status_code == 200
            assert len(response.json().get("clusters", [])) == clusters_count * 2
            SOLARClusterResponseContract(**response.json())

        @pytest.mark.parametrize(
            "auth_partner_client",
            [
                (M4W_CREDENTIALS),
                (SOLAR_CREDENTIALS),
            ],
            indirect=["auth_partner_client"],
        )
        def test_contract_solar_get_cluster_by_name(self, auth_partner_client):
            """Test that filtered GET /v1/solar/clusters response matches SOLAR contract schema."""
            azure_cluster_name = "4wm-cluster-dev-azure"
            aws_cluster_name = "4wm-cluster-dev-aws"
            AzureClusterFactory(name=azure_cluster_name)
            AWSClusterFactory(name=aws_cluster_name)
            response = auth_partner_client.get("/v1/solar/clusters", params={"name": azure_cluster_name})
            assert response.status_code == 200
            assert len(response.json().get("clusters", [])) == 1
            SOLARClusterResponseContract(**response.json())
            response = auth_partner_client.get("/v1/solar/clusters", params={"name": aws_cluster_name})
            assert response.status_code == 200
            assert len(response.json().get("clusters", [])) == 1
            SOLARClusterResponseContract(**response.json())

        @pytest.mark.parametrize(
            "auth_partner_client",
            [
                (M4W_CREDENTIALS),
                (SOLAR_CREDENTIALS),
            ],
            indirect=["auth_partner_client"],
        )
        def test_contract_solar_get_cluster_by_multi_tenant(self, auth_partner_client):
            """Test that multi_tenant filtered GET /v1/solar/clusters response matches SOLAR contract schema."""
            azure_single_tenant_count = randint(1, 10)
            aws_single_tenant_count = randint(1, 10)
            azure_multi_tenant_count = randint(1, 10)
            aws_multi_tenant_count = randint(1, 10)
            [AzureClusterFactory(multi_tenant=False) for _ in range(azure_single_tenant_count)]
            [AWSClusterFactory(multi_tenant=False) for _ in range(aws_single_tenant_count)]
            [AzureClusterFactory(multi_tenant=True) for _ in range(azure_multi_tenant_count)]
            [AWSClusterFactory(multi_tenant=True) for _ in range(aws_multi_tenant_count)]
            response = auth_partner_client.get("/v1/solar/clusters", params={"multi_tenant": True})
            assert response.status_code == 200
            assert len(response.json().get("clusters", [])) == azure_multi_tenant_count + aws_multi_tenant_count
            SOLARClusterResponseContract(**response.json())
            response = auth_partner_client.get("/v1/solar/clusters", params={"multi_tenant": False})
            assert response.status_code == 200
            assert len(response.json().get("clusters", [])) == azure_single_tenant_count + aws_single_tenant_count
            SOLARClusterResponseContract(**response.json())
