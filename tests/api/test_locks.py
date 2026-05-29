"""Lock API endpoint tests."""

from fastapi.testclient import TestClient

from tests.conftest import API
from tests.factories import make_cluster_data, make_lock_request, make_release_data


def _problem(response):
    return response.json()["detail"]


def _create_release(client: TestClient, **overrides):
    response = client.post(f"{API}/releases", json=make_release_data(**overrides))
    assert response.status_code == 201, response.json()
    return response.json()


def _create_cluster(client: TestClient, **overrides):
    response = client.post(f"{API}/clusters", json=make_cluster_data(**overrides))
    assert response.status_code == 201, response.json()
    return response.json()


def _acquire_lock(client: TestClient, cluster_name: str = "test-cluster", **overrides):
    response = client.post(
        f"{API}/clusters/{cluster_name}/lock",
        json=make_lock_request(**overrides),
    )
    assert response.status_code == 201, response.json()
    return response.json()


class TestAcquireLock:
    def test_acquire_lock_success(self, authed_client: TestClient):
        _create_release(authed_client)
        _create_cluster(authed_client)

        data = _acquire_lock(authed_client, owner="pipeline")

        assert data["cluster_name"] == "test-cluster"
        assert data["message"] == "Cluster successfully locked"
        assert "token" in data
        assert "timeout_at" in data

    def test_acquire_already_locked_returns_423(self, authed_client: TestClient):
        _create_release(authed_client)
        _create_cluster(authed_client)
        _acquire_lock(authed_client)

        response = authed_client.post(f"{API}/clusters/test-cluster/lock", json=make_lock_request())

        assert response.status_code == 423
        assert _problem(response) == {
            "title": "Cluster already locked",
            "detail": "Cluster test-cluster is already locked by another operation",
            "status": 423,
        }

    def test_acquire_nonexistent_cluster_returns_404(self, authed_client: TestClient):
        response = authed_client.post(f"{API}/clusters/nonexistent/lock", json=make_lock_request())
        assert response.status_code == 404
        assert _problem(response) == {
            "title": "Cluster not found",
            "detail": "Cluster 'nonexistent' not found",
            "status": 404,
        }

    def test_acquire_lock_with_timeout_above_limit_returns_422(self, authed_client: TestClient):
        _create_release(authed_client)
        _create_cluster(authed_client)

        response = authed_client.post(
            f"{API}/clusters/test-cluster/lock",
            json=make_lock_request(timeout_minutes=721),
        )

        assert response.status_code == 422
        assert any(item["loc"] == ["body", "timeout_minutes"] for item in response.json()["detail"])


class TestReleaseLock:
    def test_release_lock_success(self, authed_client: TestClient):
        _create_release(authed_client)
        _create_cluster(authed_client)
        token = _acquire_lock(authed_client)["token"]

        response = authed_client.request(
            "DELETE",
            f"{API}/clusters/test-cluster/lock",
            json={"token": token},
        )
        assert response.status_code == 200
        assert response.json() == {
            "cluster_name": "test-cluster",
            "message": "Cluster successfully unlocked",
        }

    def test_release_wrong_token_returns_400(self, authed_client: TestClient):
        _create_release(authed_client)
        _create_cluster(authed_client)
        _acquire_lock(authed_client)

        response = authed_client.request(
            "DELETE",
            f"{API}/clusters/test-cluster/lock",
            json={"token": "wrong-token"},
        )
        assert response.status_code == 400
        assert _problem(response) == {
            "title": "Lock token mismatch",
            "detail": "The cluster test-cluster lock token did not match",
            "status": 400,
        }

    def test_release_no_lock_returns_404(self, authed_client: TestClient):
        _create_release(authed_client)
        _create_cluster(authed_client)

        response = authed_client.request(
            "DELETE",
            f"{API}/clusters/test-cluster/lock",
            json={"token": "any-token"},
        )
        assert response.status_code == 404
        assert _problem(response) == {
            "title": "Cluster lock not found",
            "detail": "The cluster test-cluster does not have a lock",
            "status": 404,
        }

    def test_release_already_unlocked_returns_409(self, authed_client: TestClient):
        _create_release(authed_client)
        _create_cluster(authed_client)
        token = _acquire_lock(authed_client)["token"]

        response = authed_client.request(
            "DELETE",
            f"{API}/clusters/test-cluster/lock",
            json={"token": token},
        )
        assert response.status_code == 200

        response = authed_client.request(
            "DELETE",
            f"{API}/clusters/test-cluster/lock",
            json={"token": token},
        )

        assert response.status_code == 409
        assert _problem(response) == {
            "title": "Cluster not locked",
            "detail": "The cluster test-cluster is not locked",
            "status": 409,
        }


class TestListLocks:
    def test_list_empty(self, authed_client: TestClient):
        response = authed_client.get(f"{API}/locks")
        assert response.status_code == 200
        assert response.json() == {"count": 0, "items": []}

    def test_list_returns_active_lock(self, authed_client: TestClient):
        _create_release(authed_client)
        _create_cluster(authed_client)
        _acquire_lock(authed_client)

        response = authed_client.get(f"{API}/locks")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["items"][0]["cluster_name"] == "test-cluster"
        assert data["items"][0]["locked"] is True
        assert data["items"][0]["owner"] == "4wm"

    def test_list_filters_by_cluster_name(self, authed_client: TestClient):
        _create_release(authed_client)
        _create_cluster(authed_client)
        _create_cluster(authed_client, name="other-cluster")
        _acquire_lock(authed_client, owner="first-owner")
        _acquire_lock(authed_client, cluster_name="other-cluster", owner="second-owner")

        response = authed_client.get(f"{API}/locks", params={"cluster_name": "other-cluster"})

        assert response.status_code == 200
        assert response.json()["count"] == 1
        assert response.json()["items"][0]["cluster_name"] == "other-cluster"
        assert response.json()["items"][0]["owner"] == "second-owner"
