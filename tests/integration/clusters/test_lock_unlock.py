from datetime import datetime, timedelta, timezone

import pytest
from factories.cluster_factory import AWSClusterFactory, AzureClusterFactory
from sqlalchemy.orm import object_session

from api.shared.models.clusters import ClusterLock


def attach_lock(cluster, *, locked, token, owner, timeout_at, created_at, updated_at):
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


@pytest.mark.integration
@pytest.mark.cluster_lock
class TestLockCluster:
    """Integration tests for PUT /v1/clusters/{name}/lock endpoint."""

    def test_lock_cluster_success(self, auth_client):
        """Test that PUT /v1/clusters/{name}/lock locks a cluster successfully."""
        cluster = AWSClusterFactory()

        response = auth_client.put(
            f"/v1/clusters/{cluster.name}/lock",
            params={"owner": "test-owner", "timeout": 60},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Cluster succesfully locked"
        assert "token" in data

    def test_lock_already_locked_cluster(self, auth_client):
        """Test that locking an already-locked cluster returns 423."""
        cluster = attach_lock(
            AzureClusterFactory(),
            locked=True,
            token="existing-token",
            owner="other-owner",
            timeout_at=(datetime.now(tz=timezone.utc) + timedelta(hours=1)).replace(tzinfo=None),
            created_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
            updated_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
        )

        response = auth_client.put(
            f"/v1/clusters/{cluster.name}/lock",
            params={"owner": "another-owner", "timeout": 60},
        )
        assert response.status_code == 423
        assert "locked" in response.json()["detail"].lower() or "lock" in response.json()["detail"].lower()

    def test_lock_invalid_cluster_name(self, auth_client):
        """Test that locking a non-existent cluster returns 404."""
        response = auth_client.put(
            "/v1/clusters/nonexistent-cluster/lock",
            params={"owner": "test-owner", "timeout": 60},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Cluster not found"

    def test_lock_invalid_timeout_value(self, auth_client):
        """Test that an invalid timeout value returns 422."""
        cluster = AWSClusterFactory()

        response = auth_client.put(
            f"/v1/clusters/{cluster.name}/lock",
            params={"owner": "test-owner", "timeout": 9999},
        )
        assert response.status_code == 422

    def test_lock_unauthorized_access(self, unauth_client):
        """Test that locking without credentials returns 401."""
        cluster = AWSClusterFactory()

        response = unauth_client.put(
            f"/v1/clusters/{cluster.name}/lock",
            params={"owner": "test-owner", "timeout": 60},
        )
        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.cluster_lock
class TestUnlockCluster:
    """Integration tests for PUT /v1/clusters/{name}/unlock endpoint."""

    def test_unlock_cluster_success(self, auth_client):
        """Test that PUT /v1/clusters/{name}/unlock unlocks a cluster successfully."""
        cluster = AWSClusterFactory()

        # First lock the cluster
        lock_response = auth_client.put(
            f"/v1/clusters/{cluster.name}/lock",
            params={"owner": "test-owner", "timeout": 60},
        )
        assert lock_response.status_code == 200
        token = lock_response.json()["token"]

        # Now unlock with the correct token
        response = auth_client.put(
            f"/v1/clusters/{cluster.name}/unlock",
            params={"token": token},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Cluster successfully unlocked"

    def test_unlock_invalid_token(self, auth_client):
        """Test that unlocking with an invalid token returns 400."""
        cluster = attach_lock(
            AzureClusterFactory(),
            locked=True,
            token="correct-token",
            owner="test-owner",
            timeout_at=(datetime.now(tz=timezone.utc) + timedelta(hours=1)).replace(tzinfo=None),
            created_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
            updated_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
        )

        response = auth_client.put(
            f"/v1/clusters/{cluster.name}/unlock",
            params={"token": "wrong-token"},
        )
        assert response.status_code == 400
        assert "token" in response.json()["detail"].lower() or "match" in response.json()["detail"].lower()

    def test_unlock_cluster_not_locked(self, auth_client):
        """Test that unlocking a cluster that is not locked returns 409."""
        cluster = attach_lock(
            AzureClusterFactory(),
            locked=False,
            token=None,
            owner=None,
            timeout_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
            created_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
            updated_at=(datetime.now(tz=timezone.utc)).replace(tzinfo=None),
        )

        response = auth_client.put(
            f"/v1/clusters/{cluster.name}/unlock",
            params={"token": "some-token"},
        )
        assert response.status_code == 409
        assert "not locked" in response.json()["detail"].lower()

    def test_unlock_invalid_cluster_name(self, auth_client):
        """Test that unlocking a non-existent cluster returns 404."""
        response = auth_client.put(
            "/v1/clusters/nonexistent-cluster/unlock",
            params={"token": "some-token"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Cluster not found"

    def test_unlock_unauthorized_access(self, unauth_client):
        """Test that unlocking without credentials returns 401."""
        cluster = AWSClusterFactory()

        response = unauth_client.put(
            f"/v1/clusters/{cluster.name}/unlock",
            params={"token": "some-token"},
        )
        assert response.status_code == 401
