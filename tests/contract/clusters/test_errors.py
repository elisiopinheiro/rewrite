import pytest


@pytest.mark.contract
@pytest.mark.clusters4wm_app
class TestContractErrors:
    """Contract tests for cluster error responses."""

    @pytest.mark.not_found
    class TestNotFound:
        """Tests for HTTP 404 not found responses."""

        def test_contract_get_cluster_by_id_not_found(self, auth_client):
            """Test that GET /v1/clusters/{id} returns HTTP 404 for non-existent cluster."""
            response = auth_client.get("/v1/clusters/0")
            assert response.status_code == 404

        def test_contract_update_cluster_not_found(self, auth_client):
            """Test that PUT /v1/clusters/{id} returns HTTP 404 for non-existent cluster."""
            response = auth_client.put("/v1/clusters/0", json={"node_min_count": 2})
            assert response.status_code == 404

        def test_contract_backfill_cluster_not_found(self, auth_client):
            """Test that PUT /v1/clusters/{id}/backfill returns HTTP 404 for non-existent cluster."""
            backfill_data = {"domain_allowlist": ["example.com"]}
            response = auth_client.put("/v1/clusters/0/backfill", json=backfill_data)
            assert response.status_code == 404

    @pytest.mark.authorization
    class TestUnauthorized:
        """Tests for HTTP 401 unauthorized responses."""

        def test_contract_get_cluster_by_id_unauthorized(self, unauth_client):
            """Test that GET /v1/clusters/{id} returns HTTP 401 without authentication."""
            response = unauth_client.get("/v1/clusters/0")
            assert response.status_code == 401

        def test_contract_get_clusters_v1_unauthorized(self, unauth_client):
            """Test that GET /v1/clusters returns HTTP 401 without authentication."""
            response = unauth_client.get("/v1/clusters")
            assert response.status_code == 401

        def test_contract_get_clusters_v2_unauthorized(self, unauth_client):
            """Test that GET /v2/clusters returns HTTP 401 without authentication."""
            response = unauth_client.get("/v2/clusters")
            assert response.status_code == 401

        def test_contract_get_clusters_by_adgr_groups_unauthorized(self, unauth_client):
            """Test that GET /v1/clusters/adgr returns HTTP 401 without authentication."""
            response = unauth_client.get("/v1/clusters/adgr")
            assert response.status_code == 401

        def test_contract_add_cluster_unauthorized(self, unauth_client):
            """Test that POST /v1/clusters returns HTTP 401 without authentication."""
            response = unauth_client.post("/v1/clusters", json={"name": "test", "provider": "aws"})
            assert response.status_code == 401

        def test_contract_update_cluster_unauthorized(self, unauth_client):
            """Test that PUT /v1/clusters/{id} returns HTTP 401 without authentication."""
            response = unauth_client.put("/v1/clusters/0", json={"node_min_count": 2})
            assert response.status_code == 401

        def test_contract_backfill_cluster_unauthorized(self, unauth_client):
            """Test that PUT /v1/clusters/{id}/backfill returns HTTP 401 without authentication."""
            response = unauth_client.put("/v1/clusters/0/backfill", json={"domain_allowlist": ["example.com"]})
            assert response.status_code == 401
