"""Health and readiness endpoint tests for both apps."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.api.health as health_module
from app.main import app as main_app
from app.partner import app as partner_app

APPS = pytest.mark.parametrize("app", [main_app, partner_app], ids=["m4w", "partner"])


@APPS
def test_healthz_ok(app: FastAPI) -> None:
    with TestClient(app) as client:
        response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@APPS
def test_readyz_ok_when_db_available(app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(health_module, "database_is_available", lambda: True)
    with TestClient(app) as client:
        response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


@APPS
def test_readyz_503_when_db_unavailable(app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(health_module, "database_is_available", lambda: False)
    with TestClient(app) as client:
        response = client.get("/readyz")
    assert response.status_code == 503
    assert response.json()["detail"] == "Database unavailable"
