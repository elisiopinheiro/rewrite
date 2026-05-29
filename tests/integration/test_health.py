import pytest


def health_check(client):
    """Helper function to verify health endpoint returns healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == ["Healthy"]


@pytest.mark.integration
@pytest.mark.clusters4wm_app
class TestM4WHealth:
    """Integration tests for clusters-4wm API health endpoint."""

    def test_health_check(self, client):
        """Test that clusters-4wm API health endpoint returns healthy status."""
        health_check(client)


@pytest.mark.integration
@pytest.mark.partner_app
class TestPartnerHealth:
    """Integration tests for partner API health endpoint."""

    def test_partner_health_check(self, partner_client):
        """Test that partner API health endpoint returns healthy status."""
        health_check(partner_client)
