"""Cluster API endpoint tests."""

from fastapi.testclient import TestClient

from tests.conftest import API
from tests.factories import make_cluster_data, make_lock_request, make_release_data


class TestListClusters:
    def test_list_empty(self, authed_client: TestClient):
        response = authed_client.get(f"{API}/clusters")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["items"] == []

    def test_list_returns_created_cluster(self, authed_client: TestClient):
        # Create a release first (needed for feature sync)
        authed_client.post(f"{API}/releases", json=make_release_data())
        # Create cluster
        payload = make_cluster_data()
        authed_client.post(f"{API}/clusters", json=payload)

        response = authed_client.get(f"{API}/clusters")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["items"][0]["name"] == "test-cluster"

    def test_list_filter_by_provider(self, authed_client: TestClient):
        authed_client.post(f"{API}/releases", json=make_release_data(provider="aws"))
        authed_client.post(f"{API}/releases", json=make_release_data(provider="azure"))
        authed_client.post(f"{API}/clusters", json=make_cluster_data(name="aws-cluster", provider="aws"))
        authed_client.post(f"{API}/clusters", json=make_cluster_data(name="azure-cluster", provider="azure"))

        response = authed_client.get(f"{API}/clusters", params={"provider": "azure"})
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert [item["name"] for item in data["items"]] == ["azure-cluster"]
        assert data["items"][0]["provider"] == "azure"

    def test_list_filter_by_locked_state(self, authed_client: TestClient):
        authed_client.post(f"{API}/releases", json=make_release_data())
        authed_client.post(f"{API}/clusters", json=make_cluster_data(name="unlocked-cluster"))
        authed_client.post(f"{API}/clusters", json=make_cluster_data(name="locked-cluster"))

        lock_response = authed_client.post(
            f"{API}/clusters/locked-cluster/lock",
            json=make_lock_request(timeout_minutes=60),
        )
        assert lock_response.status_code == 201

        response = authed_client.get(f"{API}/clusters", params={"locked": "true"})
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert [item["name"] for item in data["items"]] == ["locked-cluster"]
        assert data["items"][0]["locked"] is True

    def test_unauthenticated_returns_401(self, client: TestClient):
        response = client.get(f"{API}/clusters")
        assert response.status_code == 401


class TestCreateCluster:
    def test_create_aws_cluster(self, authed_client: TestClient):
        authed_client.post(f"{API}/releases", json=make_release_data())
        payload = make_cluster_data()
        response = authed_client.post(f"{API}/clusters", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test-cluster"
        assert data["provider"] == "aws"
        assert data["locked"] is False
        assert data["is_in_downtime_window"] is False

    def test_create_duplicate_returns_409(self, authed_client: TestClient):
        authed_client.post(f"{API}/releases", json=make_release_data())
        payload = make_cluster_data()
        authed_client.post(f"{API}/clusters", json=payload)
        response = authed_client.post(f"{API}/clusters", json=payload)
        assert response.status_code == 409
        assert response.json()["detail"]["title"] == "Cluster already exists"

    def test_create_with_unknown_release_returns_422(self, authed_client: TestClient):
        response = authed_client.post(f"{API}/clusters", json=make_cluster_data(release="missing-release"))
        assert response.status_code == 422
        assert response.json()["detail"]["title"] == "Release not found"

    def test_create_with_nested_fields(self, authed_client: TestClient):
        authed_client.post(f"{API}/releases", json=make_release_data(provider="azure"))
        payload = make_cluster_data(
            provider="azure",
            name="azure-cluster",
            repository="https://github.com/org/azure-cluster",
            client_namespaces=[{"name": "team-a", "admin": ["APPL_TEAMA"]}],
            additional_node_pools=[{"name": "poola", "node_min_count": 1, "node_max_count": 2, "tshirt_size": "M"}],
            client_otlp_endpoints=[
                {
                    "name": "otel",
                    "endpoint_type": "otlp",
                    "endpoint": "https://example.com/otlp",
                    "signals": ["logs"],
                    "auth": {
                        "auth_type": "header",
                        "secret_name": "otel-headers",
                        "secret_namespace": "platform",
                    },
                    "config": {"required_attributes": ["k8s.cluster.name"]},
                }
            ],
            teams_webhooks={"platform": {"all": ["https://example.com/webhook"]}},
            storage_classes={
                "remote": {
                    "backup": {
                        "subscription_id": "sub-002",
                        "storage_account": "remotestorage",
                        "resource_group": "rg-storage",
                    }
                },
                "ultra_ssd": {
                    "fast": {
                        "iops": 1200,
                        "throughput": 300,
                    }
                },
            },
        )
        response = authed_client.post(f"{API}/clusters", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["client_namespaces"][0]["name"] == "team-a"
        assert data["additional_node_pools"][0]["name"] == "poola"
        endpoint = data["client_otlp_endpoints"][0]
        assert endpoint["name"] == "otel"
        assert endpoint["endpoint_type"] == "otlp"
        assert "type" not in endpoint
        assert endpoint["auth"]["auth_type"] == "header"
        assert "type" not in endpoint["auth"]
        assert endpoint["config"] == {"required_attributes": ["k8s.cluster.name"]}
        webhook = data["teams_webhooks"][0]
        assert webhook["webhook_type"] == "platform"
        assert webhook["level"] == "all"
        assert webhook["url"] == "https://example.com/webhook"
        assert "webhook_id" in webhook
        remote_storage = data["storage_classes"]["remote"]["backup"]
        assert remote_storage["subscription_id"] == "sub-002"
        assert remote_storage["storage_account"] == "remotestorage"
        assert remote_storage["resource_group"] == "rg-storage"
        assert remote_storage["sku_name"] == "Standard_LRS"
        assert data["storage_classes"]["ultra_ssd"]["fast"] == {"iops": 1200, "throughput": 300}


class TestGetCluster:
    def test_get_by_name(self, authed_client: TestClient):
        authed_client.post(f"{API}/releases", json=make_release_data())
        authed_client.post(f"{API}/clusters", json=make_cluster_data())
        response = authed_client.get(f"{API}/clusters/test-cluster")
        assert response.status_code == 200
        assert response.json()["name"] == "test-cluster"

    def test_get_nonexistent_returns_404(self, authed_client: TestClient):
        response = authed_client.get(f"{API}/clusters/nonexistent")
        assert response.status_code == 404


class TestPatchCluster:
    def test_patch_scalar_fields(self, authed_client: TestClient):
        authed_client.post(f"{API}/releases", json=make_release_data())
        authed_client.post(f"{API}/clusters", json=make_cluster_data())

        response = authed_client.patch(f"{API}/clusters/test-cluster", json={"kubernetes_version": "1.29"})
        assert response.status_code == 200
        assert response.json()["kubernetes_version"] == "1.29"

    def test_patch_can_clear_nested_fields(self, authed_client: TestClient):
        authed_client.post(f"{API}/releases", json=make_release_data())
        payload = make_cluster_data(
            client_otlp_endpoints=[
                {
                    "name": "otel",
                    "endpoint_type": "otlp",
                    "endpoint": "https://example.com/otlp",
                    "signals": ["logs"],
                }
            ],
            teams_webhooks={"platform": {"all": ["https://example.com/webhook"]}},
        )
        create_response = authed_client.post(f"{API}/clusters", json=payload)
        assert create_response.status_code == 201

        response = authed_client.patch(
            f"{API}/clusters/test-cluster",
            json={"teams_webhooks": None, "client_otlp_endpoints": []},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["teams_webhooks"] == []
        assert data["client_otlp_endpoints"] == []

    def test_patch_nonexistent_returns_404(self, authed_client: TestClient):
        response = authed_client.patch(f"{API}/clusters/nonexistent", json={"kubernetes_version": "1.29"})
        assert response.status_code == 404


class TestDeleteCluster:
    def test_delete_existing(self, authed_client: TestClient):
        authed_client.post(f"{API}/releases", json=make_release_data())
        authed_client.post(f"{API}/clusters", json=make_cluster_data())

        response = authed_client.delete(f"{API}/clusters/test-cluster")
        assert response.status_code == 200
        assert "deleted" in response.json()["message"]

        # Verify gone
        response = authed_client.get(f"{API}/clusters/test-cluster")
        assert response.status_code == 404

    def test_delete_nonexistent_returns_404(self, authed_client: TestClient):
        response = authed_client.delete(f"{API}/clusters/nonexistent")
        assert response.status_code == 404
