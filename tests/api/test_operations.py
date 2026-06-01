"""Operation API endpoint tests."""

from fastapi.testclient import TestClient

from tests.conftest import API
from tests.factories import make_cluster_data, make_operation_data, make_release_data


def _problem(response):
    """Return the RFC 7807 problem fields the tests assert on."""
    body = response.json()
    return {key: body[key] for key in ("title", "detail", "status")}


def _create_release(client: TestClient, **overrides):
    response = client.post(f"{API}/releases", json=make_release_data(**overrides))
    assert response.status_code == 201, response.json()
    return response.json()


def _create_cluster(client: TestClient, **overrides):
    response = client.post(f"{API}/clusters", json=make_cluster_data(**overrides))
    assert response.status_code == 201, response.json()
    return response.json()


def _create_operation(client: TestClient, cluster_name: str = "test-cluster", **overrides):
    response = client.post(
        f"{API}/clusters/{cluster_name}/operations",
        json=make_operation_data(**overrides),
    )
    assert response.status_code == 201, response.json()
    return response.json()


class TestOperations:
    def test_list_global_empty(self, authed_client: TestClient):
        response = authed_client.get(f"{API}/operations")
        assert response.status_code == 200
        assert response.json() == {"count": 0, "items": []}

    def test_create_operation(self, authed_client: TestClient):
        _create_release(authed_client)
        cluster = _create_cluster(authed_client)

        data = _create_operation(authed_client)

        assert data["operation_type"] == "deploy"
        assert data["status"] == "success"
        assert data["cicd_url"] == "https://ci.example.com/builds/123"
        assert data["cluster_id"] == cluster["id"]
        assert data["cluster_repository"] is None
        assert "id" in data

    def test_list_cluster_operations(self, authed_client: TestClient):
        _create_release(authed_client)
        cluster = _create_cluster(authed_client)
        operation = _create_operation(authed_client)

        response = authed_client.get(f"{API}/clusters/test-cluster/operations")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["items"] == [{**operation, "cluster_id": cluster["id"]}]

    def test_list_global_filters_by_status_and_cluster_repository(self, authed_client: TestClient):
        _create_release(authed_client)
        _create_cluster(authed_client)
        _create_operation(authed_client, status="success", cluster_repository="repo-a")
        filtered = _create_operation(authed_client, status="failed", cluster_repository="repo-b")

        response = authed_client.get(
            f"{API}/operations",
            params={"status": "failed", "cluster_repository": "repo-b"},
        )

        assert response.status_code == 200
        assert response.json() == {"count": 1, "items": [filtered]}

    def test_list_cluster_operations_for_nonexistent_cluster_returns_404(self, authed_client: TestClient):
        response = authed_client.get(f"{API}/clusters/nonexistent/operations")

        assert response.status_code == 404
        assert _problem(response) == {
            "title": "Cluster not found",
            "detail": "Cluster 'nonexistent' not found",
            "status": 404,
        }

    def test_create_operation_with_non_https_cicd_url_returns_422(self, authed_client: TestClient):
        _create_release(authed_client)
        _create_cluster(authed_client)

        response = authed_client.post(
            f"{API}/clusters/test-cluster/operations",
            json=make_operation_data(cicd_url="http://ci.example.com/builds/123"),
        )

        assert response.status_code == 422
        assert any(item["loc"] == ["body", "cicd_url"] for item in response.json()["detail"])

    def test_create_for_nonexistent_cluster_returns_404(self, authed_client: TestClient):
        response = authed_client.post(
            f"{API}/clusters/nonexistent/operations",
            json=make_operation_data(),
        )
        assert response.status_code == 404
        assert _problem(response) == {
            "title": "Cluster not found",
            "detail": "Cluster 'nonexistent' not found",
            "status": 404,
        }
