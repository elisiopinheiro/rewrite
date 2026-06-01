"""Cluster application service."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.cluster import Cluster
from app.repositories.cluster import ClusterRepository
from app.repositories.feature import FeatureRepository
from app.repositories.release import ReleaseRepository
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
    ClusterStatusSummary,
)
from app.services.clusters.mapper import ClusterMapper
from app.services.clusters.translator import ClusterTranslator
from app.services.errors import ProblemException


class ClusterService:
    def __init__(
        self,
        repository: ClusterRepository,
        feature_repository: FeatureRepository,
        release_repository: ReleaseRepository,
        session: Session,
        mapper: ClusterMapper,
        translator: ClusterTranslator,
    ) -> None:
        self.repository = repository
        self.feature_repository = feature_repository
        self.release_repository = release_repository
        self.session = session
        self.mapper = mapper
        self.translator = translator

    def _ensure_release_exists(self, *, release_name: str, provider: str) -> None:
        if self.release_repository.exists_by_name_and_provider(name=release_name.lower(), provider=provider):
            return
        raise ProblemException(title="Release not found", detail=f"Release {release_name} not found", status=422)

    def _list_filtered_clusters(self, query: ClusterListQuery) -> list[Cluster]:
        clusters = self.repository.list_clusters(order_by=query.order_by, **query.repository_filters())
        if query.locked is not None:
            clusters = [cluster for cluster in clusters if self.mapper.is_locked(cluster) is query.locked]
        return clusters

    def list_clusters(self, query: ClusterListQuery) -> ClusterListResponse:
        clusters = self._list_filtered_clusters(query)
        items = [self.mapper.to_read_model(cluster) for cluster in clusters]
        return ClusterListResponse(count=len(items), items=items)

    def get_cluster_by_name(self, cluster_name: str) -> ClusterRead:
        cluster = self.repository.get_by_name(cluster_name)
        if cluster is None:
            raise ProblemException(title="Cluster not found", detail=f"Cluster '{cluster_name}' not found", status=404)
        return self.mapper.to_read_model(cluster)

    def create_cluster(self, payload: ClusterCreate) -> ClusterRead:
        if self.repository.exists_by_name(payload.name):
            raise ProblemException(
                title="Cluster already exists",
                detail=f"Cluster '{payload.name}' already exists",
                status=409,
            )

        self._ensure_release_exists(release_name=payload.release, provider=payload.provider)

        cluster_data = payload.model_dump(
            exclude={
                "features",
                "client_namespaces",
                "additional_node_pools",
                "teams_webhooks",
                "client_otlp_endpoints",
                "storage_classes",
            }
        )
        cluster = Cluster(**cluster_data)

        try:
            self.translator.sync_nested_fields(
                cluster=cluster,
                payload=payload.model_dump(),
                feature_repository=self.feature_repository,
                release_repository=self.release_repository,
            )
            created = self.repository.add(cluster)
            self.session.commit()
        except ValueError as exc:
            self.session.rollback()
            raise ProblemException(title="Release not found", detail=str(exc), status=422) from exc
        except IntegrityError as exc:
            self.session.rollback()
            raise ProblemException(
                title="Cluster already exists",
                detail=f"Cluster '{payload.name}' already exists",
                status=409,
            ) from exc

        self.session.refresh(created)
        return self.mapper.to_read_model(created)

    def update_cluster(self, cluster_name: str, payload: ClusterPatch) -> ClusterRead:
        cluster = self.repository.get_by_name(cluster_name)
        if cluster is None:
            raise ProblemException(title="Cluster not found", detail=f"Cluster '{cluster_name}' not found", status=404)

        nested_fields = {
            "features",
            "client_namespaces",
            "additional_node_pools",
            "user_features",
            "teams_webhooks",
            "client_otlp_endpoints",
            "storage_classes",
        }
        update_data = payload.model_dump(exclude_unset=True)
        release_name = update_data.get("release", cluster.release)
        self._ensure_release_exists(release_name=release_name, provider=cluster.provider)
        self.repository.apply_scalar_updates(cluster, update_data, exclude=nested_fields)

        try:
            self.translator.sync_nested_fields(
                cluster=cluster,
                payload=update_data,
                release_name=release_name,
                feature_repository=self.feature_repository,
                release_repository=self.release_repository,
            )
            self.session.commit()
        except ValueError as exc:
            self.session.rollback()
            raise ProblemException(title="Release not found", detail=str(exc), status=422) from exc

        self.session.refresh(cluster)
        return self.mapper.to_read_model(cluster)

    def delete_cluster(self, cluster_name: str) -> ClusterDeleteResponse:
        cluster = self.repository.get_by_name(cluster_name)
        if cluster is None:
            raise ProblemException(title="Cluster not found", detail=f"Cluster '{cluster_name}' not found", status=404)
        name = cluster.name
        self.repository.delete(cluster)
        self.session.commit()
        return ClusterDeleteResponse(message=f"Cluster {name} deleted successfully")

    def list_cluster_statuses(self, query: ClusterListQuery) -> ClusterStatusListResponse:
        items = [
            ClusterStatusSummary(id=cluster.id, name=cluster.name, status=cluster.status)
            for cluster in self._list_filtered_clusters(query)
        ]
        return ClusterStatusListResponse(count=len(items), items=items)

    def update_cluster_statuses(
        self,
        query: ClusterListQuery,
        request: BulkClusterStatusUpdateRequest,
    ) -> BulkClusterStatusUpdateResponse:
        clusters = self._list_filtered_clusters(query)

        for cluster in clusters:
            cluster.status = request.status

        self.session.commit()
        updated_items = [
            ClusterStatusSummary(id=cluster.id, name=cluster.name, status=cluster.status) for cluster in clusters
        ]
        return BulkClusterStatusUpdateResponse(count=len(updated_items), items=updated_items)
