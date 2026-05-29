import pytest
from contract.clusters.schemas.cluster_backfill_v1 import ClusterBackfillRequestContractV1
from contract.clusters.schemas.cluster_request_v1 import ClusterRequestContractV1
from contract.clusters.schemas.cluster_storage_classes import StorageClassContract
from contract.clusters.schemas.cluster_update_v1 import ClusterUpdateRequestContractV1
from factories.cluster_factory import (
    AWSClusterFactory,
    AzureClusterFactory,
    make_add_cluster_payload,
    make_cluster_backfill_payload,
    make_cluster_update_payload,
)
from factories.storage_class_factory import (
    make_add_remote_storage_class_payload,
    make_add_ultra_ssd_storage_class_payload,
)
from pydantic import TypeAdapter

from api.shared.models.clusters import Provider


@pytest.mark.contract
@pytest.mark.clusters4wm_app
class TestContractRequests:
    """Contract tests for cluster request payloads."""

    def test_contract_add_cluster(self, auth_client):
        """Test that POST /v1/clusters request payloads match contract schema."""
        # Test AWS cluster request validation
        aws_cluster_data = make_add_cluster_payload(provider=Provider.AWS)
        TypeAdapter(ClusterRequestContractV1).validate_python(aws_cluster_data)
        response = auth_client.post("/v1/clusters", json=aws_cluster_data)
        assert response.status_code == 200

        # Test Azure cluster request validation
        azure_cluster_data = make_add_cluster_payload(provider=Provider.AZURE)
        TypeAdapter(ClusterRequestContractV1).validate_python(azure_cluster_data)
        response = auth_client.post("/v1/clusters", json=azure_cluster_data)
        assert response.status_code == 200

    def test_contract_update_cluster(self, auth_client):
        """Test that PUT /v1/clusters/{id} request payloads match contract schema."""
        aws_cluster = AWSClusterFactory()
        azure_cluster = AzureClusterFactory()

        update_aws_data = make_cluster_update_payload(provider=aws_cluster.provider)
        TypeAdapter(ClusterUpdateRequestContractV1).validate_python(update_aws_data)

        update_azure_data = make_cluster_update_payload(provider=azure_cluster.provider)
        TypeAdapter(ClusterUpdateRequestContractV1).validate_python(update_azure_data)

        response = auth_client.put(f"/v1/clusters/{aws_cluster.id}", json=update_aws_data)
        assert response.status_code == 200

        response = auth_client.put(f"/v1/clusters/{azure_cluster.id}", json=update_azure_data)
        assert response.status_code == 200

    def test_contract_backfill_cluster(self, auth_client):
        """Test that PUT /v1/clusters/{id}/backfill request payloads match contract schema."""
        aws_cluster = AWSClusterFactory()
        azure_cluster = AzureClusterFactory()

        backfill_aws_data = make_cluster_backfill_payload(provider=Provider.AWS)
        TypeAdapter(ClusterBackfillRequestContractV1).validate_python(backfill_aws_data)

        backfill_azure_data = make_cluster_backfill_payload(provider=Provider.AZURE)
        TypeAdapter(ClusterBackfillRequestContractV1).validate_python(backfill_azure_data)

        response = auth_client.put(f"/v1/clusters/{aws_cluster.id}/backfill", json=backfill_aws_data)
        assert response.status_code == 200

        response = auth_client.put(f"/v1/clusters/{azure_cluster.id}/backfill", json=backfill_azure_data)
        assert response.status_code == 200

    @pytest.mark.storage_classes
    class TestStorageClasses:
        """Contract tests for storage classes in cluster request payloads."""

        def test_contract_add_cluster_with_storage_classes(self, auth_client):
            """Test that POST /v1/clusters with storage classes validates request contract."""
            storage_classes_data = {
                **make_add_remote_storage_class_payload(),
                **make_add_ultra_ssd_storage_class_payload(),
            }
            TypeAdapter(StorageClassContract).validate_python(storage_classes_data)

            azure_cluster_data = make_add_cluster_payload(provider=Provider.AZURE, storage_classes=storage_classes_data)
            TypeAdapter(ClusterRequestContractV1).validate_python(azure_cluster_data)

            response = auth_client.post("/v1/clusters", json=azure_cluster_data)
            assert response.status_code == 200

        def test_contract_update_cluster_with_storage_classes(self, auth_client):
            """Test that PUT /v1/clusters/{id} with storage classes validates request contract."""
            azure_cluster = AzureClusterFactory()

            storage_classes_data = {
                **make_add_remote_storage_class_payload(),
                **make_add_ultra_ssd_storage_class_payload(),
            }
            TypeAdapter(StorageClassContract).validate_python(storage_classes_data)

            update_data = {"storage_classes": storage_classes_data}
            TypeAdapter(ClusterUpdateRequestContractV1).validate_python(update_data)

            response = auth_client.put(f"/v1/clusters/{azure_cluster.id}", json=update_data)
            assert response.status_code == 200

        def test_contract_backfill_cluster_with_storage_classes(self, auth_client):
            """Test that PUT /v1/clusters/{id}/backfill with storage classes validates request contract."""
            azure_cluster = AzureClusterFactory()

            storage_classes_data = {
                **make_add_remote_storage_class_payload(),
                **make_add_ultra_ssd_storage_class_payload(),
            }
            TypeAdapter(StorageClassContract).validate_python(storage_classes_data)

            backfill_data = {
                "domain_allowlist": ["example.com"],
                "storage_classes": storage_classes_data,
            }
            TypeAdapter(ClusterBackfillRequestContractV1).validate_python(backfill_data)

            response = auth_client.put(f"/v1/clusters/{azure_cluster.id}/backfill", json=backfill_data)
            assert response.status_code == 200

    @pytest.mark.additional_node_pools
    class TestAdditionalNodePools:
        """Contract tests for additional node pools in cluster request payloads."""

        @pytest.mark.parametrize(
            "provider",
            [Provider.AWS, Provider.AZURE],
        )
        def test_contract_add_cluster_with_additional_node_pools(self, auth_client, provider):
            """Test that POST /v1/clusters with additional node pools validates request contract."""
            additional_node_pools = [
                {"name": "nodepool1", "node_min_count": 0, "node_max_count": 1, "tshirt_size": "ram-s"}
            ]

            cluster_data = make_add_cluster_payload(provider=provider, additional_node_pools=additional_node_pools)
            TypeAdapter(ClusterRequestContractV1).validate_python(cluster_data)

            response = auth_client.post("/v1/clusters", json=cluster_data)
            assert response.status_code == 200

        @pytest.mark.parametrize(
            "provider",
            [Provider.AWS, Provider.AZURE],
        )
        def test_contract_update_cluster_with_additional_node_pools(self, auth_client, provider):
            """Test that PUT /v1/clusters/{id} with additional node pools validates request contract."""
            cluster = AWSClusterFactory() if provider == Provider.AWS else AzureClusterFactory()
            additional_node_pools = [
                {"name": "nodepool1", "node_min_count": 0, "node_max_count": 1, "tshirt_size": "ram-s"}
            ]

            update_data = {"additional_node_pools": additional_node_pools}
            TypeAdapter(ClusterUpdateRequestContractV1).validate_python(update_data)

            response = auth_client.put(f"/v1/clusters/{cluster.id}", json=update_data)
            assert response.status_code == 200

        @pytest.mark.parametrize(
            "provider",
            [Provider.AWS, Provider.AZURE],
        )
        def test_contract_backfill_cluster_with_additional_node_pools(self, auth_client, provider):
            """Test that PUT /v1/clusters/{id}/backfill with additional node pools validates request contract."""
            cluster = AWSClusterFactory() if provider == Provider.AWS else AzureClusterFactory()
            additional_node_pools = [
                {"name": "nodepool1", "node_min_count": 0, "node_max_count": 1, "tshirt_size": "ram-s"}
            ]

            backfill_data = {"additional_node_pools": additional_node_pools}
            TypeAdapter(ClusterBackfillRequestContractV1).validate_python(backfill_data)

            response = auth_client.put(f"/v1/clusters/{cluster.id}/backfill", json=backfill_data)
            assert response.status_code == 200
