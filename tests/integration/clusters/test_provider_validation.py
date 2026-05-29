"""Integration tests for cluster provider validation.

These tests verify that the provider field validation works correctly:
- Mismatched provider values should be rejected
"""

import pytest
from factories.cluster_factory import make_add_cluster_payload
from fastapi import status

from api.shared.models.clusters import Provider


@pytest.mark.integration
@pytest.mark.clusters4wm_app
class TestProviderValidation:
    """Integration tests for cluster provider validation."""

    class TestAWSProvider:
        """Tests for AWS provider validation."""

        def test_add_cluster_aws_with_correct_provider(self, auth_client, db_session):
            """Test that AWS cluster with provider=AWS is accepted."""
            cluster_data = make_add_cluster_payload(Provider.AWS)

            response = auth_client.post("/v1/clusters", json=cluster_data)

            assert response.status_code == status.HTTP_200_OK
            response_data = response.json()
            assert response_data["provider"] == Provider.AWS.value
            assert response_data["aws_vpc"] == cluster_data["aws_vpc"]

        def test_add_cluster_aws_fields_with_azure_provider_fails(self, auth_client, db_session):
            """Test that AWS cluster fields with provider=AZURE is rejected."""
            # Create AWS cluster data then override provider to 'azure'
            cluster_data = make_add_cluster_payload(Provider.AWS)
            cluster_data["provider"] = Provider.AZURE.value

            response = auth_client.post("/v1/clusters", json=cluster_data)

            assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

            response_data = response.json()
            assert "detail" in response_data

        def test_pydantic_model_validation_aws_with_wrong_provider(self):
            """Test that Pydantic ClusterAws model rejects provider=AZURE."""
            from pydantic import ValidationError

            from api.shared.models.clusters import ClusterAws

            with pytest.raises(ValidationError) as exc_info:
                ClusterAws(
                    name="test-cluster",
                    subscription="test-sub",
                    account_name="test-account",
                    provider=Provider.AZURE.value,  # Wrong provider!
                    release="1.0",
                    environment="development",
                    internal=True,
                    repository="test-repo",
                    node_min_count=1,
                    node_max_count=3,
                    provider_region="eu-central-1",
                    tshirt_size="s",
                    infra_revision="1.0.0",
                    kubernetes_version="1.30",
                    network_cidr="10.0.0.0/8",
                    aws_vpc="vpc-123456",
                )

            errors = exc_info.value.errors()
            assert any("provider" in str(error).lower() for error in errors)

    class TestAzureProvider:
        """Tests for Azure provider validation."""

        def test_add_cluster_azure_with_correct_provider(self, auth_client, db_session):
            """Test that Azure cluster with provider=AZURE is accepted."""
            cluster_data = make_add_cluster_payload(Provider.AZURE)

            response = auth_client.post("/v1/clusters", json=cluster_data)

            assert response.status_code == status.HTTP_200_OK
            response_data = response.json()
            assert response_data["provider"] == Provider.AZURE.value
            assert response_data["azure_sku_tier"] == cluster_data["azure_sku_tier"]

        def test_add_cluster_azure_fields_with_aws_provider_fails(self, auth_client, db_session):
            """Test that Azure cluster fields with provider=AWS is rejected."""
            # Create Azure cluster data then override provider to 'aws'
            cluster_data = make_add_cluster_payload(Provider.AZURE)
            cluster_data["provider"] = Provider.AWS.value

            response = auth_client.post("/v1/clusters", json=cluster_data)

            assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

            response_data = response.json()
            assert "detail" in response_data

        def test_pydantic_model_validation_azure_with_wrong_provider(self):
            """Test that Pydantic ClusterAzure model rejects provider=AWS."""
            from pydantic import ValidationError

            from api.shared.models.clusters import ClusterAzure

            with pytest.raises(ValidationError) as exc_info:
                ClusterAzure(
                    name="test-cluster",
                    subscription="test-sub",
                    account_name="test-account",
                    provider=Provider.AWS.value,  # Wrong provider!
                    release="1.0",
                    environment="development",
                    internal=True,
                    repository="test-repo",
                    node_min_count=1,
                    node_max_count=3,
                    provider_region="eu-central-1",
                    tshirt_size="s",
                    infra_revision="1.0.0",
                    kubernetes_version="1.30",
                    network_cidr="10.0.0.0/8",
                    azure_sku_tier="Free",
                    azure_subnet_name="test-subnet",
                    azure_vnet_name="test-vnet",
                    azure_vnet_resource_group="test-rg",
                    dns_service_ip="10.0.0.10",
                    mi_agentpool_object_id="test-id-1",
                    mi_cluster_object_id="test-id-2",
                )

            errors = exc_info.value.errors()
            assert any("provider" in str(error).lower() for error in errors)
