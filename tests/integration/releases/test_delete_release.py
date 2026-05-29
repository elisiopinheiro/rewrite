import pytest
from factories.release_factory import ReleaseFactory

from api.shared.models.clusters import Provider


@pytest.mark.integration
@pytest.mark.clusters4wm_app
@pytest.mark.releases
class TestDeleteRelease:
    """Integration tests for DELETE /v1/releases/{id} endpoint."""

    def test_delete_release_success(self, auth_client):
        """Test that DELETE /v1/releases/{id} deletes a release."""
        release = ReleaseFactory(name="release-to-delete", provider=Provider.AWS)

        response = auth_client.delete(f"/v1/releases/{release.id}")
        assert response.status_code == 200

        response_data = response.json()
        assert "msg" in response_data
        assert "deleted successfully" in response_data["msg"]
        assert release.name in response_data["msg"]

    def test_delete_release_not_found(self, auth_client):
        """Test that deleting non-existent release returns HTTP 404."""
        # Try to delete a non-existent release
        non_existent_id = 999999
        response = auth_client.delete(f"/v1/releases/{non_existent_id}")
        assert response.status_code == 404
        assert "Release not found" in response.json()["detail"]

    def test_delete_release_and_verify_gone(self, auth_client):
        """Test that deleted release can no longer be retrieved."""
        release = ReleaseFactory(name="release-to-verify-delete", provider=Provider.AWS)

        # Verify release exists
        response = auth_client.get(f"/v1/releases/{release.provider}/{release.name}")
        assert response.status_code == 200

        # Delete the release
        response = auth_client.delete(f"/v1/releases/{release.id}")
        assert response.status_code == 200

        # Verify release no longer exists
        response = auth_client.get(f"/v1/releases/{release.provider}/{release.name}")
        assert response.status_code == 404

    def test_delete_one_release_keeps_others(self, auth_client):
        """Test that deleting one release does not affect other releases."""
        release1 = ReleaseFactory(name="aws1", provider=Provider.AWS)
        release2 = ReleaseFactory(name="aws2", provider=Provider.AWS)
        release3 = ReleaseFactory(name="azure1", provider=Provider.AZURE)

        # Delete one release
        response = auth_client.delete(f"/v1/releases/{release2.id}")
        assert response.status_code == 200

        # Verify others still exist
        response = auth_client.get(f"/v1/releases/{release1.provider}/{release1.name}")
        assert response.status_code == 200

        response = auth_client.get(f"/v1/releases/{release3.provider}/{release3.name}")
        assert response.status_code == 200

        # Verify deleted release no longer exists
        response = auth_client.get(f"/v1/releases/{release2.provider}/{release2.name}")
        assert response.status_code == 404
