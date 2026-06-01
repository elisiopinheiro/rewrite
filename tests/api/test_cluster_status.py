"""Tests for the bulk cluster status endpoints (GET/PATCH /clusters/status)."""

from fastapi.testclient import TestClient

from tests.conftest import API
from tests.factories import make_cluster_data, make_release_data


def _seed_two_clusters(client: TestClient) -> None:
    client.post(f"{API}/releases", json=make_release_data(provider="aws"))
    client.post(f"{API}/releases", json=make_release_data(provider="azure"))
    client.post(f"{API}/clusters", json=make_cluster_data(name="aws-cluster", provider="aws"))
    client.post(f"{API}/clusters", json=make_cluster_data(name="azure-cluster", provider="azure"))


class TestListClusterStatuses:
    def test_lists_summaries(self, authed_client: TestClient):
        _seed_two_clusters(authed_client)

        response = authed_client.get(f"{API}/clusters/status")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert {item["name"] for item in data["items"]} == {"aws-cluster", "azure-cluster"}
        assert all(item["status"] == "running" for item in data["items"])
        assert set(data["items"][0]) == {"id", "name", "status"}

    def test_filter_returns_empty(self, authed_client: TestClient):
        _seed_two_clusters(authed_client)
        response = authed_client.get(f"{API}/clusters/status", params={"name": "nope"})
        assert response.status_code == 200
        assert response.json() == {"count": 0, "items": []}

    def test_requires_auth(self, client: TestClient):
        assert client.get(f"{API}/clusters/status").status_code == 401


class TestUpdateClusterStatuses:
    def test_bulk_update_only_matching_subset(self, authed_client: TestClient):
        _seed_two_clusters(authed_client)

        response = authed_client.patch(
            f"{API}/clusters/status",
            params={"provider": "azure"},
            json={"status": "freeze"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["items"][0]["name"] == "azure-cluster"
        assert data["items"][0]["status"] == "freeze"

        # The non-matching cluster is untouched.
        statuses = {c["name"]: c["status"] for c in authed_client.get(f"{API}/clusters/status").json()["items"]}
        assert statuses == {"aws-cluster": "running", "azure-cluster": "freeze"}

    def test_invalid_status_returns_422(self, authed_client: TestClient):
        response = authed_client.patch(f"{API}/clusters/status", json={"status": "bogus"})
        assert response.status_code == 422
