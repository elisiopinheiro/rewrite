"""Clusters partner application"""

from typing import Union

from fastapi import Depends, FastAPI
from fastapi import status as http_status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.sql.elements import BinaryExpression

from api.partner.auth import Role, validate_credentials, validate_user_role
from api.partner.models.scp import SCPClusterFilters, SCPClusterFiltersAzure, SCPClusterList
from api.partner.models.solar import SOLARClusterFilters, SOLARClusterList
from api.shared.config import APP_ENVIRONMENT, APP_VERSION
from api.shared.logger import logger
from api.shared.metrics_setup import setup_metrics
from api.shared.repository.cluster_repository import ClusterRepository

CLUSTERS_NOT_FOUND = {"message": "No clusters found"}

app = FastAPI(
    version=APP_VERSION,
    title=f"4Wheels Managed Clusters API for specific services - {APP_ENVIRONMENT.title()}",
    description="API for specific services to read 4Wheels Managed Clusters information",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
)

setup_metrics(app)


class Message(BaseModel):
    """Message class"""

    message: str


@app.get("/health", include_in_schema=False)
def health():
    """Health check"""
    return {"Healthy"}


@app.get(
    "/v1/clusters",
    response_model=SCPClusterList,
    responses={404: {"model": Message}},
    dependencies=[Depends(validate_user_role(allowed_roles=[Role.SCP, Role.CF]))],
    tags=["CF and SCP"],
)
def list_clusters(
    filters: SCPClusterFilters = Depends(),
    username: str = Depends(validate_credentials),
    cluster_repository: ClusterRepository = Depends(ClusterRepository),
) -> Union[SCPClusterList, JSONResponse]:
    """
    \f Method to list clusters

    Args:
        filters (SCPClusterFilters, optional): Filters. Defaults to Depends().
        username (str, optional): Username. Defaults to Depends(validate_credentials).

    Returns:
        SCPClusterList: List of clusters
        JSONResponse: 404 response if no clusters are found
    """
    logger.info("Received GET /v1/clusters request by user: %s", username)
    azure_filter = SCPClusterFiltersAzure(**filters.model_dump())
    conditions: list[BinaryExpression] = azure_filter.prepare_filters()

    clusters = cluster_repository.get_clusters_v2(
        condition_filters=conditions,
        locked=None,
        order_by="id",
    )

    if not clusters:
        return JSONResponse(
            status_code=http_status.HTTP_404_NOT_FOUND,
            content=CLUSTERS_NOT_FOUND,
        )
    return SCPClusterList(count=len(clusters), clusters=clusters)


@app.get(
    "/v1/solar/clusters",
    response_model=SOLARClusterList,
    responses={404: {"model": Message}},
    dependencies=[Depends(validate_user_role(allowed_roles=[Role.SOLAR]))],
    tags=["SOLAR"],
)
def solar_list_clusters(
    filters: SOLARClusterFilters = Depends(),
    username: str = Depends(validate_credentials),
    cluster_repository: ClusterRepository = Depends(ClusterRepository),
) -> Union[SOLARClusterList, JSONResponse]:
    """
    \f Method to list clusters

    Args:
        filters (SOLARClusterFilters, optional): Filters. Defaults to Depends().
        username (str, optional): Username. Defaults to Depends(validate_credentials).

    Returns:
        SOLARClusterList: List of client clusters
        JSONResponse: 404 response if no clusters are found
    """
    logger.info("Received GET /v1/solar/clusters request by user: %s", username)
    client_clusters_filter = SOLARClusterFilters(**filters.model_dump())
    conditions: list[BinaryExpression] = client_clusters_filter.prepare_filters()

    clusters = cluster_repository.get_clusters_v2(
        condition_filters=conditions,
        order_by="id",
    )

    if not clusters:
        return JSONResponse(
            status_code=http_status.HTTP_404_NOT_FOUND,
            content=CLUSTERS_NOT_FOUND,
        )
    return SOLARClusterList(count=len(clusters), clusters=clusters)
