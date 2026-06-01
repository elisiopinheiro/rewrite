"""Regression tests for migration-sensitive cluster behavior."""

from fastapi.testclient import TestClient
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models.lock import ClusterLock
from tests.conftest import API
from tests.factories import make_cluster_data, make_lock_request, make_release_data


class TestNullableProviderFields:
    def test_aws_cluster_with_null_optional_fields_serializes(self, authed_client: TestClient):
        # The factory omits vpc_endpoint_service_name/oidc fields, which persist as NULL.
        authed_client.post(f"{API}/releases", json=make_release_data())
        authed_client.post(f"{API}/clusters", json=make_cluster_data())

        response = authed_client.get(f"{API}/clusters/test-cluster")
        assert response.status_code == 200
        data = response.json()
        assert data["vpc_endpoint_service_name"] is None
        assert data["vpc_endpoint_service_ingress_name"] is None
        assert data["cluster_oidc_issuer_url"] is None
        assert data["aws_vpc"] == "vpc-12345"


class TestHeadlampEnabled:
    def test_round_trips(self, authed_client: TestClient):
        authed_client.post(f"{API}/releases", json=make_release_data())
        created = authed_client.post(f"{API}/clusters", json=make_cluster_data())
        assert created.json()["headlamp_enabled"] is False

        patched = authed_client.patch(f"{API}/clusters/test-cluster", json={"headlamp_enabled": True})
        assert patched.status_code == 200
        assert patched.json()["headlamp_enabled"] is True


class TestPatchFeaturesNoOp:
    def test_empty_features_list_does_not_wipe_features(self, authed_client: TestClient):
        authed_client.post(f"{API}/releases", json=make_release_data(features=[{"name": "logging"}]))
        authed_client.post(
            f"{API}/clusters",
            json=make_cluster_data(features=[{"name": "logging", "feature_type": "optional", "enabled": True}]),
        )

        before = authed_client.get(f"{API}/clusters/test-cluster").json()
        assert [f["name"] for f in before["features"]] == ["logging"]

        # An explicit empty list must be a no-op (legacy semantics), not a wipe.
        response = authed_client.patch(f"{API}/clusters/test-cluster", json={"features": []})
        assert response.status_code == 200

        after = authed_client.get(f"{API}/clusters/test-cluster").json()
        assert [f["name"] for f in after["features"]] == ["logging"]


class TestClusterLockCascade:
    def test_db_level_delete_cascades_to_lock(self, authed_client: TestClient, session: Session):
        authed_client.post(f"{API}/releases", json=make_release_data())
        authed_client.post(f"{API}/clusters", json=make_cluster_data())
        authed_client.post(f"{API}/clusters/test-cluster/lock", json=make_lock_request())
        assert session.scalar(select(func.count()).select_from(ClusterLock)) == 1

        # A DB-level DELETE exercises the FK ondelete=CASCADE, not just the ORM relationship.
        session.execute(text("DELETE FROM cluster WHERE name = 'test-cluster'"))
        session.commit()

        assert session.scalar(select(func.count()).select_from(ClusterLock)) == 0
