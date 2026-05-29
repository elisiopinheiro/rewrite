"""Lock repository — data access for cluster locks."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.cluster import Cluster
from app.models.lock import ClusterLock


class LockRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(
        self,
        *,
        cluster_name: str | None = None,
        owner: str | None = None,
        token: str | None = None,
    ) -> list[ClusterLock]:
        statement = select(ClusterLock).options(selectinload(ClusterLock.cluster))

        if cluster_name is not None:
            statement = statement.join(ClusterLock.cluster).where(Cluster.name == cluster_name)
        if owner is not None:
            statement = statement.where(ClusterLock.owner == owner)
        if token is not None:
            statement = statement.where(ClusterLock.token == token)

        return list(self.session.scalars(statement).all())

    def get(self, cluster_id: int) -> ClusterLock | None:
        return self.session.get(ClusterLock, cluster_id)

    def get_for_update(self, cluster_id: int) -> ClusterLock | None:
        statement = select(ClusterLock).where(ClusterLock.cluster_id == cluster_id).with_for_update(nowait=True)
        return self.session.scalars(statement).one_or_none()

    def add(self, lock: ClusterLock) -> ClusterLock:
        self.session.add(lock)
        return lock

    def clear(self, lock: ClusterLock) -> ClusterLock:
        now = datetime.now(UTC).replace(tzinfo=None)
        lock.owner = None
        lock.token = None
        lock.timeout_at = now
        lock.updated_at = now
        lock.locked = False
        return lock
