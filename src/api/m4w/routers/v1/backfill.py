"""Backfill router methods"""

from typing import Annotated, Union

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from pydantic import Field as PydanticField

from api.m4w.auth import validate_backfill_credentials
from api.shared.exceptions import ReleaseNotFoundException
from api.shared.logger import logger
from api.shared.models.clusters import (
    ClusterAwsResponse,
    ClusterAzureResponse,
    ClusterUpdateBackfill,
)
from api.shared.models.httperror import HTTPError
from api.shared.repository.cluster_repository import ClusterRepository

ClusterResponse = Annotated[
    Union[ClusterAwsResponse, ClusterAzureResponse],
    PydanticField(discriminator="provider"),
]

router = APIRouter(prefix="/v1/clusters", tags=["Backfill"])


@router.put(
    "/{id}/backfill",
    responses={404: {"model": HTTPError}, 422: {"model": HTTPError}},
    response_model=ClusterResponse,
)
def backfill_cluster(
    id: int,
    backfill_data: ClusterUpdateBackfill,
    username: str = Depends(validate_backfill_credentials),
    cluster_repository: ClusterRepository = Depends(ClusterRepository),
) -> ClusterResponse:
    """
    \f Update cluster's backfill data

    Args:
        id (int): Cluster ID
        backfill_data (ClusterUpdateBackfill): Backfill data
        username (str, optional): Username. Defaults to Depends(validate_backfill_credentials).
        cluster_repository (ClusterRepository, optional): Cluster repository. Defaults to Depends(ClusterRepository).

    Raises:
        HTTPException: HTTP_404_NOT_FOUND if cluster does not exist
        HTTPException: HTTP_422_UNPROCESSABLE_CONTENT if release not found

    Returns:
        Union[ClusterAwsResponse, ClusterAzureResponse]: Updated cluster
    """
    logger.info("Received PUT /v1/clusters/%s/backfill request - body: %s", id, backfill_data.model_dump())
    cluster = cluster_repository.get_cluster(id)
    if cluster is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Cluster not found",
        )

    try:
        return cluster_repository.update_cluster(cluster=cluster, update_data=backfill_data)
    except ReleaseNotFoundException as e:
        logger.exception("")
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(e),
        ) from e
