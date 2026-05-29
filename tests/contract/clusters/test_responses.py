from typing import List

import pytest
from contract.clusters.schemas.cluster_response_v1 import (
    AWSClusterResponseContractV1,
    AzureClusterResponseContractV1,
    ClusterResponseContractV1,
)
from contract.clusters.schemas.cluster_response_v2 import ClusterResponseContractV2
from contract.clusters.schemas.cluster_storage_classes import StorageClassContract
from factories.cluster_factory import (
    AWSClusterFactory,
    AzureClusterFactory,
    ClientNamespaceFactory,
    make_add_cluster_payload,
)
from factories.storage_class_factory import (
    RemoteStorageClassFactory,
    UltraSSDStorageClassFactory,
    make_add_remote_storage_class_payload,
    make_add_ultra_ssd_storage_class_payload,
)
from pydantic import TypeAdapter

from api.shared.models.clusters import Provider


@pytest.mark.contract
@pytest.mark.clusters4wm_app
class TestContractResponses:
    """Contract tests for cluster response payloads."""

    def test_contract_get_cluster_by_id(self, auth_client):
        """Test that GET /v1/clusters/{id} response matches contract schema."""
        aws_cluster = AWSClusterFactory()
        azure_cluster = AzureClusterFactory()

        response = auth_client.get(f"/v1/clusters/{aws_cluster.id}")
        assert response.status_code == 200

        AWSClusterResponseContractV1(**response.json())

        response = auth_client.get(f"/v1/clusters/{azure_cluster.id}")
        assert response.status_code == 200

        AzureClusterResponseContractV1(**response.json())

    def test_contract_get_clusters_v1(self, auth_client):
        """Test that GET /v1/clusters response matches contract schema."""
        AWSClusterFactory.create_batch(2)
        AzureClusterFactory.create_batch(2)

        response = auth_client.get("/v1/clusters")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

        TypeAdapter(List[ClusterResponseContractV1]).validate_python(response.json())

    def test_contract_get_clusters_v2(self, auth_client):
        """Test that GET /v2/clusters response matches contract schema."""
        AWSClusterFactory.create_batch(2)
        AzureClusterFactory.create_batch(2)

        response = auth_client.get("/v2/clusters")
        assert response.status_code == 200

        TypeAdapter(ClusterResponseContractV2).validate_python(response.json())

    def test_contract_get_clusters_by_adgr_groups(self, auth_client):
        """Test that GET /v1/clusters/adgr response matches contract schema."""
        aws_cluster = AWSClusterFactory()
        azure_cluster = AzureClusterFactory()

        ClientNamespaceFactory(cluster_id=aws_cluster.id)
        ClientNamespaceFactory(cluster_id=azure_cluster.id, viewer=["APPL_CNAP_default_view"])

        # Test with single ADGR group
        response = auth_client.get("/v1/clusters/adgr?adgr_group=APPL_CNAP_default_view")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) == 1

        TypeAdapter(List[ClusterResponseContractV1]).validate_python(response.json())

        # Test with multiple ADGR groups
        response = auth_client.get("/v1/clusters/adgr?adgr_group=APPL_4WM_default_admin,APPL_CNAP_default_view")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) == 2

        TypeAdapter(List[ClusterResponseContractV1]).validate_python(response.json())

        # Test with non-existent ADGR group
        response = auth_client.get("/v1/clusters/adgr?adgr_group=APPL_NONEXISTENT")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) == 0

    def test_contract_add_cluster(self, auth_client):
        """Test that POST /v1/clusters response matches contract schema."""
        aws_cluster_data = make_add_cluster_payload(provider=Provider.AWS)
        response = auth_client.post("/v1/clusters", json=aws_cluster_data)
        assert response.status_code == 200
        TypeAdapter(ClusterResponseContractV1).validate_python(response.json())

        azure_cluster_data = make_add_cluster_payload(provider=Provider.AZURE)
        response = auth_client.post("/v1/clusters", json=azure_cluster_data)
        assert response.status_code == 200
        TypeAdapter(ClusterResponseContractV1).validate_python(response.json())

    def test_contract_update_cluster(self, auth_client):
        """Test that PUT /v1/clusters/{id} response matches contract schema."""
        aws_cluster = AWSClusterFactory()

        response = auth_client.put(f"/v1/clusters/{aws_cluster.id}", json={"node_min_count": 2})
        assert response.status_code == 200
        TypeAdapter(ClusterResponseContractV1).validate_python(response.json())

    def test_contract_backfill_cluster(self, auth_client):
        """Test that PUT /v1/clusters/{id}/backfill response matches contract schema."""
        aws_cluster = AWSClusterFactory()

        backfill_data = {
            "domain_allowlist": ["example.com", "test.com"],
        }

        response = auth_client.put(f"/v1/clusters/{aws_cluster.id}/backfill", json=backfill_data)
        assert response.status_code == 200
        TypeAdapter(ClusterResponseContractV1).validate_python(response.json())

    @pytest.mark.storage_classes
    class TestStorageClasses:
        """Contract tests for storage classes in cluster responses."""

        def test_contract_get_azure_cluster_with_storage_classes(self, auth_client):
            """Test that GET /v1/clusters/{id} with storage classes matches contract schema."""
            azure_cluster = AzureClusterFactory()
            RemoteStorageClassFactory(cluster_id=azure_cluster.id)
            UltraSSDStorageClassFactory(cluster_id=azure_cluster.id)

            response = auth_client.get(f"/v1/clusters/{azure_cluster.id}")
            assert response.status_code == 200
            response_data = response.json()
            TypeAdapter(AzureClusterResponseContractV1).validate_python(response_data)
            assert response_data.get("storage_classes") is not None
            TypeAdapter(StorageClassContract).validate_python(response_data["storage_classes"])

        def test_contract_add_azure_cluster_with_storage_classes(self, auth_client):
            """Test that POST /v1/clusters with storage classes matches contract schema."""
            azure_cluster_data = make_add_cluster_payload(
                provider=Provider.AZURE,
                storage_classes={
                    **make_add_remote_storage_class_payload(),
                    **make_add_ultra_ssd_storage_class_payload(),
                },
            )

            response = auth_client.post("/v1/clusters", json=azure_cluster_data)
            assert response.status_code == 200
            response_data = response.json()
            TypeAdapter(AzureClusterResponseContractV1).validate_python(response_data)
            assert response_data.get("storage_classes") is not None
            TypeAdapter(StorageClassContract).validate_python(response_data["storage_classes"])

        def test_contract_update_azure_cluster_with_storage_classes(self, auth_client):
            """Test that PUT /v1/clusters/{id} with storage classes matches contract schema."""
            azure_cluster = AzureClusterFactory()
            update_data = {
                "storage_classes": {
                    **make_add_remote_storage_class_payload(),
                    **make_add_ultra_ssd_storage_class_payload(),
                }
            }

            response = auth_client.put(f"/v1/clusters/{azure_cluster.id}", json=update_data)
            assert response.status_code == 200
            response_data = response.json()
            TypeAdapter(AzureClusterResponseContractV1).validate_python(response_data)
            assert response_data.get("storage_classes") is not None
            TypeAdapter(StorageClassContract).validate_python(response_data["storage_classes"])

        def test_contract_backfill_azure_cluster_with_storage_classes(self, auth_client):
            """Test that PUT /v1/clusters/{id}/backfill with storage classes matches contract schema."""
            azure_cluster = AzureClusterFactory()
            backfill_data = {
                "domain_allowlist": ["example.com"],
                "storage_classes": {
                    **make_add_remote_storage_class_payload(),
                    **make_add_ultra_ssd_storage_class_payload(),
                },
            }

            response = auth_client.put(f"/v1/clusters/{azure_cluster.id}/backfill", json=backfill_data)
            assert response.status_code == 200
            response_data = response.json()
            TypeAdapter(AzureClusterResponseContractV1).validate_python(response_data)
            assert response_data.get("storage_classes") is not None
            TypeAdapter(StorageClassContract).validate_python(response_data["storage_classes"])
