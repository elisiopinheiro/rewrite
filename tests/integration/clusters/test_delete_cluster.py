import pytest
from factories.cluster_factory import (
    AdditionalNodePoolFactory,
    AWSClusterFactory,
    AzureClusterFactory,
)
from factories.storage_class_factory import RemoteStorageClassFactory, UltraSSDStorageClassFactory

from api.shared.enums import Provider
from api.shared.models.storage_classes import StorageClass, StorageClassType


@pytest.mark.integration
@pytest.mark.clusters4wm_app
class TestDeleteCluster:
    """Integration tests for DELETE /v1/clusters/{id} endpoint."""

    @pytest.mark.parametrize(
        "provider",
        [Provider.AWS, Provider.AZURE],
    )
    def test_delete_cluster(self, auth_client, provider):
        """Test that DELETE /v1/clusters/{id} deletes a cluster."""
        cluster = AWSClusterFactory() if provider == Provider.AWS else AzureClusterFactory()

        response = auth_client.delete(f"/v1/clusters/{cluster.id}")
        assert response.status_code == 200

    @pytest.mark.storage_classes
    class TestStorageClasses:
        """Tests for cascade deletion of remote storage classes."""

        @pytest.mark.remote_storage_classes
        class TestRemoteStorageClasses:
            def test_delete_cluster_cascades_to_remote_storage_classes(self, auth_client, db_session):
                """Test that deleting a cluster also deletes its remote storage classes."""
                azure_cluster = AzureClusterFactory()
                RemoteStorageClassFactory(cluster_id=azure_cluster.id)

                response = auth_client.get(f"/v1/clusters/{azure_cluster.id}")
                assert response.status_code == 200
                assert isinstance(response.json(), dict)
                assert "storage_classes" in response.json()
                assert "remote" in response.json()["storage_classes"]
                assert len(response.json()["storage_classes"]["remote"]) == 1

                # Verify storage class exists
                storage_classes = (
                    db_session.query(StorageClass)
                    .filter_by(cluster_id=azure_cluster.id, type=StorageClassType.AZ_CABS)
                    .all()
                )
                assert len(storage_classes) == 1
                storage_class_id = storage_classes[0].id

                delete_response = auth_client.delete(f"/v1/clusters/{azure_cluster.id}")
                assert delete_response.status_code == 200
                # Verify storage class on db was also deleted
                deleted_storage_class = db_session.get(StorageClass, storage_class_id)
                assert deleted_storage_class is None

        @pytest.mark.ultra_ssd_storage_classes
        class TestUltraSsdStorageClasses:
            """Tests for cascade deletion of Ultra SSD storage classes."""

            def test_delete_cluster_cascades_to_ultra_ssd_storage_classes(self, auth_client, db_session):
                """Test that deleting a cluster also deletes its Ultra SSD storage classes."""
                azure_cluster = AzureClusterFactory()
                UltraSSDStorageClassFactory(cluster_id=azure_cluster.id)

                response = auth_client.get(f"/v1/clusters/{azure_cluster.id}")
                assert response.status_code == 200
                assert isinstance(response.json(), dict)
                assert "storage_classes" in response.json()
                assert "ultra_ssd" in response.json()["storage_classes"]
                assert len(response.json()["storage_classes"]["ultra_ssd"]) == 1

                # Verify storage class exists
                storage_classes = (
                    db_session.query(StorageClass)
                    .filter_by(cluster_id=azure_cluster.id, type=StorageClassType.AZ_USSD)
                    .all()
                )
                assert len(storage_classes) == 1
                storage_class_id = storage_classes[0].id

                delete_response = auth_client.delete(f"/v1/clusters/{azure_cluster.id}")
                assert delete_response.status_code == 200
                # Verify storage class on db was also deleted
                deleted_storage_class = db_session.get(StorageClass, storage_class_id)
                assert deleted_storage_class is None

    @pytest.mark.additional_node_pools
    class TestAdditionalNodePools:
        @pytest.mark.parametrize(
            "provider",
            ["aws", "azure"],
        )
        def test_delete_cluster_cascades_to_additional_node_pools(self, auth_client, db_session, provider):
            """Test that deleting a cluster also deletes its additional node pools."""
            cluster = AWSClusterFactory() if provider == "aws" else AzureClusterFactory()
            AdditionalNodePoolFactory(cluster_id=cluster.id)

            response = auth_client.get(f"/v1/clusters/{cluster.id}")
            assert response.status_code == 200
            assert isinstance(response.json(), dict)
            assert "additional_node_pools" in response.json()
            assert len(response.json()["additional_node_pools"]) == 1

            delete_response = auth_client.delete(f"/v1/clusters/{cluster.id}")
            assert delete_response.status_code == 200

    def test_delete_cluster_not_found(self, auth_client):
        """Test that deleting a non-existent cluster returns 404."""
        response = auth_client.delete("/v1/clusters/999999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Cluster not found"

    def test_delete_cluster_unauthorized(self, unauth_client):
        """Test that deleting a cluster without credentials returns 401."""
        cluster = AWSClusterFactory()
        response = unauth_client.delete(f"/v1/clusters/{cluster.id}")
        assert response.status_code == 401
