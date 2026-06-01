"""Cluster repository — data access for clusters."""

from __future__ import annotations

from typing import Any

from sqlalchemy import asc, select
from sqlalchemy.orm import InstrumentedAttribute, Session, selectinload

from app.models.cluster import Cluster, ClusterFeature
from app.schemas.enums import ClusterOrderBy

_CLUSTER_LOAD_OPTIONS: tuple[Any, ...] = (
    selectinload(Cluster.features).selectinload(ClusterFeature.feature),
    selectinload(Cluster.client_namespaces),
    selectinload(Cluster.additional_node_pools),
    selectinload(Cluster.user_features),
    selectinload(Cluster.teams_webhooks),
    selectinload(Cluster.client_otlp_endpoints),
    selectinload(Cluster.storage_classes),
    selectinload(Cluster.cluster_lock),
)

_CLUSTER_ORDER_COLUMNS: dict[ClusterOrderBy, InstrumentedAttribute[Any]] = {
    ClusterOrderBy.ID: Cluster.id,
    ClusterOrderBy.NAME: Cluster.name,
    ClusterOrderBy.CMDB_APP_ID: Cluster.cmdb_app_id,
}


class ClusterRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_clusters(self, *, order_by: ClusterOrderBy = ClusterOrderBy.ID, **filters: Any) -> list[Cluster]:
        order_column = _CLUSTER_ORDER_COLUMNS.get(order_by, Cluster.id)
        statement = select(Cluster).options(*_CLUSTER_LOAD_OPTIONS).filter_by(**filters).order_by(asc(order_column))
        return list(self.session.execute(statement).unique().scalars().all())

    def get_by_id(self, cluster_id: int) -> Cluster | None:
        return self.session.get(Cluster, cluster_id)

    def get_by_name(self, name: str) -> Cluster | None:
        statement = select(Cluster).options(*_CLUSTER_LOAD_OPTIONS).where(Cluster.name == name)
        return self.session.execute(statement).unique().scalar_one_or_none()

    def exists_by_name(self, name: str) -> bool:
        statement = select(Cluster.id).where(Cluster.name == name)
        return self.session.execute(statement).first() is not None

    def add(self, cluster: Cluster) -> Cluster:
        self.session.add(cluster)
        return cluster

    def delete(self, cluster: Cluster) -> None:
        self.session.delete(cluster)

    def apply_scalar_updates(self, cluster: Cluster, data: dict[str, Any], *, exclude: set[str]) -> None:
        """Apply simple scalar field updates from a dict, skipping excluded keys."""
        for key, value in data.items():
            if key in exclude:
                continue
            if hasattr(cluster, key):
                setattr(cluster, key, value)
