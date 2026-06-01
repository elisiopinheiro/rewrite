import pytest
from factories.release_factory import ReleaseFactory
from sqlmodel import select

from api.shared.models.clusters import Provider
from api.shared.models.features import Feature


@pytest.mark.integration
@pytest.mark.clusters4wm_app
@pytest.mark.releases
class TestUpdateRelease:
    """Integration tests for PATCH /v1/releases/{id} endpoint."""

    def test_update_release_reserved_namespaces(self, auth_client):
        """Test that PATCH updates reserved_namespaces."""
        release = ReleaseFactory(provider=Provider.AWS)

        new_namespaces = ["updated-ns-1", "updated-ns-2"]
        patch_res = auth_client.patch(
            f"/v1/releases/{release.id}",
            json={"reserved_namespaces": new_namespaces},
        )

        assert patch_res.status_code == 200
        assert patch_res.json()["reserved_namespaces"] == new_namespaces
        assert patch_res.json()["name"] == release.name

    def test_update_release_features(self, auth_client):
        """Test that PATCH replaces features list."""
        release = ReleaseFactory(provider=Provider.AWS)

        new_features = [
            {"name": "patched-feature", "type": "core", "dependencies": [], "constraints": []},
        ]
        patch_res = auth_client.patch(
            f"/v1/releases/{release.id}",
            json={"features": new_features},
        )

        assert patch_res.status_code == 200
        assert len(patch_res.json()["features"]) == 1
        assert patch_res.json()["features"][0]["name"] == "patched-feature"

    def test_update_two_releases_reuses_same_feature(self, auth_client, db_session):
        """Test that updating two releases with identical features reuse the same DB feature record."""
        release1 = ReleaseFactory(provider=Provider.AWS)
        release2 = ReleaseFactory(provider=Provider.AWS)

        features = [
            {
                "name": "shared-core-feature",
                "type": "core",
                "dependencies": ["dep-one"],
            },
            {
                "name": "shared-optional-feature",
                "type": "optional",
            },
        ]
        statement = select(Feature).where(Feature.name.in_({feature["name"] for feature in features}))

        # Update first release with features
        patch_res1 = auth_client.patch(
            f"/v1/releases/{release1.id}",
            json={"features": features},
        )
        assert patch_res1.status_code == 200
        matching = db_session.execute(statement).scalars().all()
        assert len(matching) == 2

        # Update second release with same features
        patch_res2 = auth_client.patch(
            f"/v1/releases/{release2.id}",
            json={"features": features},
        )
        assert patch_res2.status_code == 200
        matching = db_session.execute(statement).scalars().all()
        assert len(matching) == 2

    def test_update_release_partial_no_change(self, auth_client):
        """Test that PATCH with empty body changes nothing."""
        release = ReleaseFactory(provider=Provider.AWS)
        original = auth_client.get("/v2/releases/", params={"name": release.name, "provider": release.provider}).json()[
            0
        ]
        print("Original release data:", original)

        patch_res = auth_client.patch(
            f"/v1/releases/{release.id}",
            json={},
        )

        assert patch_res.status_code == 200
        patched = patch_res.json()
        assert patched["reserved_namespaces"] == original["reserved_namespaces"]
        assert len(patched["features"]) == len(original["features"])

    def test_update_release_clear_features(self, auth_client):
        """Test that PATCH with empty features list clears all features."""
        release = ReleaseFactory(provider=Provider.AWS)

        patch_res = auth_client.patch(
            f"/v1/releases/{release.id}",
            json={"features": []},
        )

        assert patch_res.status_code == 200
        assert patch_res.json()["features"] == []

    def test_update_release_not_found(self, auth_client):
        """Test that PATCH on nonexistent release returns 404."""
        patch_res = auth_client.patch(
            "/v1/releases/999999",
            json={"reserved_namespaces": ["ns"]},
        )

        assert patch_res.status_code == 404

    def test_update_release_unauthorized(self, unauth_client):
        """Test that PATCH without credentials returns 401."""
        patch_res = unauth_client.patch(
            "/v1/releases/1",
            json={"reserved_namespaces": ["ns"]},
        )

        assert patch_res.status_code == 401
