from datetime import datetime, timedelta, timezone

import pytest
from factories.cluster_factory import AWSClusterFactory, AzureClusterFactory

from api.shared.models.clusters import ClusterLock


@pytest.mark.integration
@pytest.mark.clusters4wm_app
@pytest.mark.cluster_lock
class TestGetLocksV2:
    """Integration tests for GET /v2/locks endpoint."""

    def test_get_locks_v2_returns_all_locks(self, auth_client):
        """Test that GET /v2/locks returns all cluster locks."""
        AWSClusterFactory(
            cluster_lock=ClusterLock(
                locked=True,
                token="token-1",
                owner="owner-1",
                timeout_at=(datetime.now(tz=timezone.utc) + timedelta(hours=1)).replace(tzinfo=None),
                created_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
                updated_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
            )
        )
        AzureClusterFactory(
            cluster_lock=ClusterLock(
                locked=False,
                token=None,
                owner=None,
                timeout_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
                created_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
                updated_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
            )
        )

        response = auth_client.get("/v2/locks")
        assert response.status_code == 200

        response_data = response.json()
        assert isinstance(response_data, list)
        assert len(response_data) == 2

    def test_get_locks_v2_filter_by_locked(self, auth_client):
        """Test that GET /v2/locks can filter by locked status."""
        AWSClusterFactory(
            cluster_lock=ClusterLock(
                locked=True,
                token="token-1",
                owner="owner-1",
                timeout_at=(datetime.now(tz=timezone.utc) + timedelta(hours=1)).replace(tzinfo=None),
                created_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
                updated_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
            )
        )
        AzureClusterFactory(
            cluster_lock=ClusterLock(
                locked=False,
                token=None,
                owner=None,
                timeout_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
                created_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
                updated_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
            )
        )

        response = auth_client.get("/v2/locks?locked=true")
        assert response.status_code == 200

        response_data = response.json()
        assert isinstance(response_data, list)
        assert len(response_data) == 1
        assert response_data[0]["locked"] is True

    def test_get_locks_v2_filter_by_cluster_name(self, auth_client):
        """Test that GET /v2/locks can filter by cluster name."""
        cluster = AWSClusterFactory(
            cluster_lock=ClusterLock(
                locked=True,
                token="token-1",
                owner="owner-1",
                timeout_at=(datetime.now(tz=timezone.utc) + timedelta(hours=1)).replace(tzinfo=None),
                created_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
                updated_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
            )
        )
        AzureClusterFactory(
            cluster_lock=ClusterLock(
                locked=True,
                token="token-2",
                owner="owner-2",
                timeout_at=(datetime.now(tz=timezone.utc) + timedelta(hours=1)).replace(tzinfo=None),
                created_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
                updated_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
            )
        )

        response = auth_client.get(f"/v2/locks?cluster_name={cluster.name}")
        assert response.status_code == 200

        response_data = response.json()
        assert isinstance(response_data, list)
        assert len(response_data) == 1
        assert response_data[0]["cluster_name"] == cluster.name

    def test_get_locks_v2_empty_database(self, auth_client):
        """Test that GET /v2/locks returns 200 with empty list when no locks exist."""
        response = auth_client.get("/v2/locks")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_locks_v2_no_matching_filter(self, auth_client):
        """Test that GET /v2/locks returns 200 with empty list when no locks match filter."""
        AWSClusterFactory(
            cluster_lock=ClusterLock(
                locked=True,
                token="token-1",
                owner="owner-1",
                timeout_at=(datetime.now(tz=timezone.utc) + timedelta(hours=1)).replace(tzinfo=None),
                created_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
                updated_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
            )
        )

        response = auth_client.get("/v2/locks?cluster_name=nonexistent-cluster")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_locks_v2_unauthorized(self, unauth_client):
        """Test that GET /v2/locks without credentials returns 401."""
        response = unauth_client.get("/v2/locks")
        assert response.status_code == 401
