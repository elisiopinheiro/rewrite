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
