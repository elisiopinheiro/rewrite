import pytest
from factories.feature_factory import FeatureFactory, make_add_feature_payload


@pytest.mark.integration
@pytest.mark.clusters4wm_app
@pytest.mark.optional_features
class TestOptionalFeatures:
    """Integration tests for GET /v1/features endpoint."""

    @pytest.mark.parametrize("should_create, expected_status", [(False, 404), (True, 200)])
    def test_get_features(self, auth_client, should_create, expected_status):
        """Test that GET /v1/features returns features or 404 if none exist."""
        features = []
        if should_create:
            features = FeatureFactory.create_batch(5)

        res = auth_client.get("/v1/features")
        assert res.status_code == expected_status

        if not should_create:
            assert res.json()["detail"] == "Features not found"

        for i, feature in enumerate(features):
            assert feature.name == res.json()[i]["name"]

    def test_add_feature(self, auth_client):
        """Test that POST /v1/features creates a new feature."""
        fake_feature = make_add_feature_payload()
        res = auth_client.post("/v1/features", json=fake_feature.model_dump())
        assert res.status_code == 200
        assert res.json()["name"] == fake_feature.name

    def test_add_duplicate_feature_returns_existing(self, auth_client):
        """Test that POST /v1/features with identical data returns existing feature, not a duplicate."""
        feature_data = make_add_feature_payload(
            name="dedup-feature",
            type="optional",
            dependencies=["dep-a", "dep-b"],
            constraints=[],
            namespaced=False,
        )

        res1 = auth_client.post("/v1/features", json=feature_data.model_dump())
        assert res1.status_code == 200
        feature1 = res1.json()

        res2 = auth_client.post("/v1/features", json=feature_data.model_dump())
        assert res2.status_code == 200
        feature2 = res2.json()

        assert feature1["id"] == feature2["id"]
        assert feature1["name"] == feature2["name"]

    def test_add_feature_different_deps_creates_new(self, auth_client):
        """Test that features with same name but different dependencies are distinct."""
        base = {
            "name": "shared-name",
            "type": "optional",
            "constraints": [],
            "namespaced": False,
        }

        res1 = auth_client.post("/v1/features", json={**base, "dependencies": ["dep-a"]})
        assert res1.status_code == 200

        res2 = auth_client.post("/v1/features", json={**base, "dependencies": ["dep-b"]})
        assert res2.status_code == 200

        assert res1.json()["id"] != res2.json()["id"]

    def test_add_feature_different_constraints_creates_new(self, auth_client):
        """Test that features with same name but different constraints are distinct."""
        base = {
            "name": "shared-name",
            "type": "optional",
            "dependencies": [],
            "namespaced": False,
        }

        res1 = auth_client.post(
            "/v1/features",
            json={
                **base,
                "constraints": [{"key": "env", "operator": "equals", "value": "prod"}],
            },
        )
        assert res1.status_code == 200

        res2 = auth_client.post(
            "/v1/features",
            json={
                **base,
                "constraints": [{"key": "env", "operator": "equals", "value": "dev"}],
            },
        )
        assert res2.status_code == 200

        assert res1.json()["id"] != res2.json()["id"]

    def test_delete_feature(self, auth_client):
        """Test that DELETE /v1/features/{id} deletes a feature."""
        feature = FeatureFactory.create()
        res = auth_client.delete(f"/v1/features/{feature.id}")
        assert res.status_code == 200

    def test_add_feature_invalid_payload(self, auth_client):
        """Test that POST /v1/features with invalid payload returns 422."""
        res = auth_client.post("/v1/features", json={"invalid_field": "value"})
        assert res.status_code == 422

    def test_get_features_unauthorized(self, unauth_client):
        """Test that GET /v1/features without credentials returns 401."""
        res = unauth_client.get("/v1/features")
        assert res.status_code == 401

    def test_add_feature_unauthorized(self, unauth_client):
        """Test that POST /v1/features without credentials returns 401."""
        fake_feature = make_add_feature_payload()
        res = unauth_client.post("/v1/features", json=fake_feature.model_dump())
        assert res.status_code == 401

    def test_delete_feature_unauthorized(self, unauth_client):
        """Test that DELETE /v1/features/{id} without credentials returns 401."""
        feature = FeatureFactory.create()
        res = unauth_client.delete(f"/v1/features/{feature.id}")
        assert res.status_code == 401
