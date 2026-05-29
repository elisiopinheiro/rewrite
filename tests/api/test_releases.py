"""Release and Feature API endpoint tests."""

from fastapi.testclient import TestClient

from tests.conftest import API
from tests.factories import make_feature_data, make_release_data


def _problem(response):
    return response.json()["detail"]


def _create_feature(client: TestClient, **overrides):
    response = client.post(f"{API}/features", json=make_feature_data(**overrides))
    assert response.status_code == 201, response.json()
    return response.json()


def _create_release(client: TestClient, **overrides):
    response = client.post(f"{API}/releases", json=make_release_data(**overrides))
    assert response.status_code == 201, response.json()
    return response.json()


class TestFeatures:
    def test_list_empty(self, authed_client: TestClient):
        response = authed_client.get(f"{API}/features")
        assert response.status_code == 200
        assert response.json() == {"count": 0, "items": []}

    def test_create_feature(self, authed_client: TestClient):
        data = _create_feature(authed_client)
        assert data["name"] == "monitoring"
        assert data["feature_type"] == "optional"
        assert "id" in data

    def test_create_duplicate_feature_returns_409(self, authed_client: TestClient):
        _create_feature(authed_client)

        response = authed_client.post(f"{API}/features", json=make_feature_data())

        assert response.status_code == 409
        assert _problem(response) == {
            "title": "Feature already exists",
            "detail": "Feature already exists",
            "status": 409,
        }

    def test_create_feature_with_extra_field_returns_422(self, authed_client: TestClient):
        response = authed_client.post(
            f"{API}/features",
            json={**make_feature_data(), "unexpected": True},
        )

        assert response.status_code == 422
        assert any(item["loc"] == ["body", "unexpected"] for item in response.json()["detail"])

    def test_delete_feature(self, authed_client: TestClient):
        feature_id = _create_feature(authed_client)["id"]
        response = authed_client.delete(f"{API}/features/{feature_id}")
        assert response.status_code == 200
        assert response.json() == {"message": "Feature monitoring deleted successfully"}

    def test_delete_nonexistent_returns_404(self, authed_client: TestClient):
        response = authed_client.delete(f"{API}/features/99999")
        assert response.status_code == 404
        assert _problem(response) == {
            "title": "Feature not found",
            "detail": "Feature not found",
            "status": 404,
        }


class TestReleases:
    def test_list_empty(self, authed_client: TestClient):
        response = authed_client.get(f"{API}/releases")
        assert response.status_code == 200
        assert response.json() == {"count": 0, "items": []}

    def test_create_release(self, authed_client: TestClient):
        data = _create_release(authed_client)
        assert data["name"] == "v1.0"
        assert data["provider"] == "aws"
        assert data["reserved_namespaces"] == ["kube-system"]
        assert data["features"] == []
        assert "id" in data

    def test_create_release_with_features(self, authed_client: TestClient):
        payload = make_release_data(features=[make_feature_data(name="logging")])
        response = authed_client.post(f"{API}/releases", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert len(data["features"]) == 1
        assert data["features"][0]["name"] == "logging"
        assert data["features"][0]["feature_type"] == "optional"

    def test_create_release_reuses_matching_existing_feature(self, authed_client: TestClient):
        feature = _create_feature(authed_client, name="logging")

        response = authed_client.post(
            f"{API}/releases",
            json=make_release_data(features=[make_feature_data(name="logging")]),
        )

        assert response.status_code == 201
        data = response.json()
        assert data["features"] == [feature]

        features_response = authed_client.get(f"{API}/features")
        assert features_response.status_code == 200
        assert features_response.json()["count"] == 1

    def test_create_duplicate_release_returns_409(self, authed_client: TestClient):
        _create_release(authed_client)

        response = authed_client.post(f"{API}/releases", json=make_release_data())

        assert response.status_code == 409
        assert _problem(response) == {
            "title": "Release already exists",
            "detail": "Release already exists",
            "status": 409,
        }

    def test_create_release_with_invalid_provider_returns_422(self, authed_client: TestClient):
        response = authed_client.post(f"{API}/releases", json=make_release_data(provider="gcp"))

        assert response.status_code == 422
        assert any(item["loc"] == ["body", "provider"] for item in response.json()["detail"])

    def test_get_release_by_id(self, authed_client: TestClient):
        release_id = _create_release(authed_client)["id"]
        response = authed_client.get(f"{API}/releases/{release_id}")
        assert response.status_code == 200
        assert response.json() == {
            "id": release_id,
            "name": "v1.0",
            "provider": "aws",
            "reserved_namespaces": ["kube-system"],
            "features": [],
        }

    def test_delete_release(self, authed_client: TestClient):
        release_id = _create_release(authed_client)["id"]
        response = authed_client.delete(f"{API}/releases/{release_id}")
        assert response.status_code == 200
        assert response.json() == {"message": "Release v1.0 deleted successfully"}

    def test_get_nonexistent_returns_404(self, authed_client: TestClient):
        response = authed_client.get(f"{API}/releases/99999")
        assert response.status_code == 404
        assert _problem(response) == {
            "title": "Release not found",
            "detail": "Release not found",
            "status": 404,
        }
