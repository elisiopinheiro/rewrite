"""Clusters 4WM application"""

from fastapi import FastAPI

from api.m4w.routers.v1 import backfill, clusters, features, locks, operations, releases, status
from api.m4w.routers.v2 import clusters as clusters_v2
from api.m4w.routers.v2 import features as features_v2
from api.m4w.routers.v2 import locks as locks_v2
from api.m4w.routers.v2 import operations as operations_v2
from api.m4w.routers.v2 import releases as releases_v2
from api.shared.config import APP_ENVIRONMENT, APP_VERSION
from api.shared.metrics_setup import setup_metrics

app = FastAPI(
    version=APP_VERSION,
    title=f"4Wheels Managed Clusters API - {APP_ENVIRONMENT.title()}",
    description="API for managing 4Wheels Managed Clusters",
    openapi_tags=[
        {"name": "default"},
        {"name": "Clusters v1"},
        {"name": "Clusters v2"},
        {"name": "Releases v1"},
        {"name": "Releases v2"},
        {"name": "Status"},
        {"name": "Backfill"},
        {"name": "Locks v1"},
        {"name": "Locks v2"},
        {"name": "Operations v1"},
        {"name": "Operations v2"},
        {"name": "Features v1"},
        {"name": "Features v2"},
    ],
)

setup_metrics(app)


@app.get("/health", include_in_schema=False)
def health():
    """Health check"""
    return {"Healthy"}


# Router include order controls endpoint ordering in Swagger UI.
# v2 endpoints are placed directly after their v1 counterparts.
# Static paths must be included before path parameter routers
# to avoid /{id} matching literal segments like /adgr, /status, /releases, etc.
app.include_router(clusters.router)
app.include_router(clusters_v2.router)
app.include_router(status.router)
app.include_router(clusters.router_with_id)
app.include_router(operations.router_cluster_ops)
app.include_router(locks.router_lock_unlock)
app.include_router(releases.router)
app.include_router(releases_v2.router)
app.include_router(operations.router)
app.include_router(operations_v2.router)
app.include_router(locks.router)
app.include_router(locks_v2.router)
app.include_router(backfill.router)
app.include_router(features.router)
app.include_router(features_v2.router)
