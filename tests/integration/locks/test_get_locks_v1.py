from datetime import datetime, timedelta, timezone

import pytest
from factories.cluster_factory import AWSClusterFactory, AzureClusterFactory
from sqlalchemy.orm import object_session

from api.shared.models.clusters import ClusterLock


@pytest.mark.integration
@pytest.mark.clusters4wm_app
@pytest.mark.cluster_lock
class TestGetLocksV1:
    """Integration tests for GET /v1/locks endpoint."""

    @staticmethod
    def _attach_lock(cluster, *, locked, token, owner, timeout_at, created_at, updated_at):
        cluster.cluster_lock = ClusterLock(
            cluster_id=cluster.id,
            locked=locked,
            token=token,
            owner=owner,
            timeout_at=timeout_at,
            created_at=created_at,
            updated_at=updated_at,
        )
        cluster.cluster_lock.cluster = cluster

        session = object_session(cluster)
        session.add(cluster.cluster_lock)
        session.commit()
        session.refresh(cluster)
        session.refresh(cluster.cluster_lock)
        return cluster

    def test_get_locks_v1_returns_all_locks(self, auth_client):
        """Test that GET /v1/locks returns all cluster locks."""
        self._attach_lock(
            AWSClusterFactory(),
            locked=True,
            token="token-1",
            owner="owner-1",
            timeout_at=(datetime.now(tz=timezone.utc) + timedelta(hours=1)).replace(tzinfo=None),
            created_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
            updated_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
        )
        self._attach_lock(
            AzureClusterFactory(),
            locked=False,
            token=None,
            owner=None,
            timeout_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
            created_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
            updated_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
        )

        response = auth_client.get("/v1/locks")
        assert response.status_code == 200

        response_data = response.json()
        assert isinstance(response_data, list)
        assert len(response_data) == 2

    def test_get_locks_v1_empty_database_returns_404(self, auth_client):
        """Test that GET /v1/locks returns 404 when no locks exist."""
        response = auth_client.get("/v1/locks")
        assert response.status_code == 404
        assert response.json()["detail"] == "No locks found"

    def test_get_locks_v1_no_matching_filter_returns_404(self, auth_client):
        """Test that GET /v1/locks returns 404 when no locks match filter."""
        self._attach_lock(
            AWSClusterFactory(),
            locked=True,
            token="token-1",
            owner="owner-1",
            timeout_at=(datetime.now(tz=timezone.utc) + timedelta(hours=1)).replace(tzinfo=None),
            created_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
            updated_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
        )

        response = auth_client.get("/v1/locks?cluster_name=nonexistent-cluster")
        assert response.status_code == 404
        assert response.json()["detail"] == "No locks found"
