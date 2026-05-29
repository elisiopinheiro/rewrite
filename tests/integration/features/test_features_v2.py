import pytest
from factories.feature_factory import FeatureFactory


@pytest.mark.integration
@pytest.mark.clusters4wm_app
@pytest.mark.optional_features
class TestGetFeaturesV2:
    """Integration tests for GET /v2/features endpoint."""

    @pytest.mark.parametrize("expected_count", [(0), (5)])
    def test_get_features_v2(self, auth_client, expected_count):
        """Test that GET /v2/features returns features or empty list if none exist."""
        features = FeatureFactory.create_batch(expected_count)

        res = auth_client.get("/v2/features")
        assert res.status_code == 200

        response_data = res.json()
        assert isinstance(response_data, list)
        assert len(response_data) == expected_count

        for i, feature in enumerate(features):
            assert feature.name == response_data[i]["name"]

    def test_get_features_v2_empty_database(self, auth_client):
        """Test that GET /v2/features returns 200 with empty list when no features exist."""
        res = auth_client.get("/v2/features")
        assert res.status_code == 200
        assert res.json() == []

    def test_get_features_v2_unauthorized(self, unauth_client):
        """Test that GET /v2/features without credentials returns 401."""
        res = unauth_client.get("/v2/features")
        assert res.status_code == 401
