"""Cluster API routes."""

from typing import Annotated

from fastapi import APIRouter, Query, status

from app.deps import ClusterSvc, M4WUser
from app.schemas.clusters import (
    BulkClusterStatusUpdateRequest,
    BulkClusterStatusUpdateResponse,
    ClusterCreate,
    ClusterDeleteResponse,
    ClusterListQuery,
    ClusterListResponse,
    ClusterPatch,
    ClusterRead,
    ClusterStatusListResponse,
)

router = APIRouter(prefix="/clusters", tags=["clusters"])

ClusterFilters = Annotated[ClusterListQuery, Query()]


# --- Static routes MUST come before dynamic {cluster_name} to avoid path collision ---


@router.get("/status", response_model=ClusterStatusListResponse)
def list_cluster_statuses(
    _user: M4WUser,
    service: ClusterSvc,
    query: ClusterFilters,
) -> ClusterStatusListResponse:
    return service.list_cluster_statuses(query)


@router.patch("/status", response_model=BulkClusterStatusUpdateResponse)
def update_cluster_statuses(
    _user: M4WUser,
    service: ClusterSvc,
    request: BulkClusterStatusUpdateRequest,
    query: ClusterFilters,
) -> BulkClusterStatusUpdateResponse:
    return service.update_cluster_statuses(query, request)


# --- Collection routes ---


@router.get("", response_model=ClusterListResponse)
def list_clusters(
    _user: M4WUser,
    service: ClusterSvc,
    query: ClusterFilters,
) -> ClusterListResponse:
    return service.list_clusters(query)


@router.post("", response_model=ClusterRead, status_code=status.HTTP_201_CREATED)
def create_cluster(
    _user: M4WUser,
    service: ClusterSvc,
    payload: ClusterCreate,
) -> ClusterRead:
    return service.create_cluster(payload)


# --- Resource routes (identified by cluster_name) ---


@router.get("/{cluster_name}", response_model=ClusterRead)
def get_cluster(
    cluster_name: str,
    _user: M4WUser,
    service: ClusterSvc,
) -> ClusterRead:
    return service.get_cluster_by_name(cluster_name)


@router.patch("/{cluster_name}", response_model=ClusterRead)
def update_cluster(
    cluster_name: str,
    _user: M4WUser,
    service: ClusterSvc,
    payload: ClusterPatch,
) -> ClusterRead:
    return service.update_cluster(cluster_name, payload)


@router.delete("/{cluster_name}", response_model=ClusterDeleteResponse)
def delete_cluster(
    cluster_name: str,
    _user: M4WUser,
    service: ClusterSvc,
) -> ClusterDeleteResponse:
    return service.delete_cluster(cluster_name)
