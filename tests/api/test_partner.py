"""Partner API endpoint tests."""

import base64

import pytest
from fastapi.testclient import TestClient

from app.core.db import get_db
from app.main import app as main_app
from app.partner import app as partner_app
from tests.conftest import API
from tests.factories import make_cluster_data, make_release_data


def _auth_header(username: str, password: str) -> dict[str, str]:
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {credentials}"}


def _override_apps_db(session, *, include_main: bool = False) -> None:
    def _override_get_db():
        yield session

    partner_app.dependency_overrides[get_db] = _override_get_db
    if include_main:
        main_app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
def _clear_dependency_overrides():
    yield
    main_app.dependency_overrides.clear()
    partner_app.dependency_overrides.clear()


class TestPartnerRoutes:
    def test_solar_list_empty(self, session):
        _override_apps_db(session)

        with TestClient(partner_app) as client:
            response = client.get(f"{API}/partners/solar/clusters", headers=_auth_header("solar", "solar"))
            assert response.status_code == 200
            assert response.json() == {"count": 0, "items": []}

    def test_solar_list_respects_provider_filter_and_response_shape(self, session):
        _override_apps_db(session, include_main=True)

        with TestClient(main_app) as main_client, TestClient(partner_app) as partner_client:
            main_client.headers.update(_auth_header("4wm", "4wm"))
            main_client.post(f"{API}/releases", json=make_release_data(provider="aws"))
            main_client.post(f"{API}/releases", json=make_release_data(provider="azure"))
            main_client.post(f"{API}/clusters", json=make_cluster_data(name="aws-cluster", provider="aws"))
            main_client.post(f"{API}/clusters", json=make_cluster_data(name="azure-cluster", provider="azure"))

            response = partner_client.get(
                f"{API}/partners/solar/clusters",
                params={"provider": "azure"},
                headers=_auth_header("solar", "solar"),
            )
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 1
            item = data["items"][0]
            assert set(item) == {
                "id",
                "name",
                "subscription",
                "account_name",
                "provider",
                "multi_tenant",
                "provider_region",
                "cmdb_app_id",
                "cmdb_appd_id",
            }
            assert item["name"] == "azure-cluster"
            assert item["provider"] == "azure"
            assert item["multi_tenant"] is False

    def test_scp_list_excludes_internal_and_non_azure_clusters(self, session):
        _override_apps_db(session, include_main=True)

        with TestClient(main_app) as main_client, TestClient(partner_app) as partner_client:
            main_client.headers.update(_auth_header("4wm", "4wm"))
            main_client.post(f"{API}/releases", json=make_release_data(provider="aws"))
            main_client.post(f"{API}/releases", json=make_release_data(provider="azure"))
            main_client.post(f"{API}/clusters", json=make_cluster_data(name="aws-cluster", provider="aws"))
            main_client.post(f"{API}/clusters", json=make_cluster_data(name="public-azure", provider="azure"))
            main_client.post(
                f"{API}/clusters",
                json=make_cluster_data(name="internal-azure", provider="azure", internal=True),
            )

            response = partner_client.get(
                f"{API}/partners/scp/clusters",
                headers=_auth_header("scp", "scp"),
            )
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 1
            item = data["items"][0]
            assert set(item) == {
                "id",
                "name",
                "subscription",
                "provider_region",
                "azure_vnet_name",
                "azure_vnet_resource_group",
                "network_cidr",
                "cmdb_app_id",
                "cmdb_appd_id",
            }
            assert item["name"] == "public-azure"
            assert item["azure_vnet_name"] == "vnet-1"

    def test_solar_route_forbids_scp_user(self, session):
        _override_apps_db(session)

        with TestClient(partner_app) as client:
            response = client.get(f"{API}/partners/solar/clusters", headers=_auth_header("scp", "scp"))
            assert response.status_code == 403
            assert response.json()["detail"] == "You do not have the necessary permissions to access this resource."
