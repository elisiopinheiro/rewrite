"""Cluster lock application service."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.models.lock import ClusterLock
from app.repositories.cluster import ClusterRepository
from app.repositories.lock import LockRepository
from app.schemas.locks import (
    AcquireClusterLockRequest,
    AcquireClusterLockResponse,
    ClusterLockListResponse,
    ClusterLockQuery,
    ClusterLockRead,
    ReleaseClusterLockRequest,
    ReleaseClusterLockResponse,
)
from app.services.errors import ProblemException


class ClusterLockService:
    def __init__(self, repository: LockRepository, cluster_repository: ClusterRepository, session: Session) -> None:
        self.repository = repository
        self.cluster_repository = cluster_repository
        self.session = session

    def list_locks(self, query: ClusterLockQuery) -> ClusterLockListResponse:
        locks = self.repository.list_locks(cluster_name=query.cluster_name, owner=query.owner, token=query.token)
        now = self._current_time()
        items: list[ClusterLockRead] = []
        for lock in locks:
            is_locked = self._is_lock_active(lock, now)
            if query.locked is not None and is_locked is not query.locked:
                continue
            items.append(
                ClusterLockRead(
                    cluster_name=lock.cluster.name,
                    locked=is_locked,
                    owner=lock.owner,
                    timeout_at=lock.timeout_at,
                    created_at=lock.created_at,
                    updated_at=lock.updated_at,
                )
            )
        return ClusterLockListResponse(count=len(items), items=items)

    def acquire_lock(
        self, cluster_name: str, request: AcquireClusterLockRequest, username: str
    ) -> AcquireClusterLockResponse:
        cluster = self.cluster_repository.get_by_name(cluster_name)
        if cluster is None:
            raise ProblemException(title="Cluster not found", detail=f"Cluster '{cluster_name}' not found", status=404)

        owner = request.owner or username
        now = self._current_time()
        timeout_at = now + timedelta(minutes=request.timeout_minutes)
        token = str(uuid4())

        try:
            lock = self.repository.get_for_update(cluster.id)
        except OperationalError as exc:
            self.session.rollback()
            raise ProblemException(
                title="Lock acquisition failed",
                detail="Could not acquire cluster lock",
                status=423,
            ) from exc

        if lock is None:
            lock = ClusterLock(
                cluster_id=cluster.id,
                locked=True,
                owner=owner,
                token=token,
                timeout_at=timeout_at,
                created_at=now,
                updated_at=now,
            )
            self.repository.add(lock)
        else:
            if self._is_lock_active(lock, now):
                raise ProblemException(
                    title="Cluster already locked",
                    detail=f"Cluster {cluster_name} is already locked by another operation",
                    status=423,
                )
            lock.owner = owner
            lock.token = token
            lock.updated_at = now
            lock.locked = True
            lock.timeout_at = timeout_at

        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ProblemException(
                title="Cluster already locked",
                detail=f"Cluster {cluster_name} is already locked by another operation",
                status=423,
            ) from exc
        except OperationalError as exc:
            self.session.rollback()
            raise ProblemException(
                title="Lock acquisition failed",
                detail="Could not acquire cluster lock",
                status=423,
            ) from exc

        return AcquireClusterLockResponse(
            cluster_name=cluster_name,
            message="Cluster successfully locked",
            token=token,
            timeout_at=timeout_at,
        )

    def release_lock(self, cluster_name: str, request: ReleaseClusterLockRequest) -> ReleaseClusterLockResponse:
        cluster = self.cluster_repository.get_by_name(cluster_name)
        if cluster is None:
            raise ProblemException(title="Cluster not found", detail=f"Cluster '{cluster_name}' not found", status=404)

        try:
            lock = self.repository.get_for_update(cluster.id)
        except OperationalError as exc:
            self.session.rollback()
            raise ProblemException(
                title="Lock release failed",
                detail="Cluster is being locked by another operation",
                status=423,
            ) from exc

        if lock is None:
            raise ProblemException(
                title="Cluster lock not found",
                detail=f"The cluster {cluster_name} does not have a lock",
                status=404,
            )
        if not self._is_lock_active(lock, self._current_time()):
            raise ProblemException(
                title="Cluster not locked",
                detail=f"The cluster {cluster_name} is not locked",
                status=409,
            )
        if lock.token != request.token:
            raise ProblemException(
                title="Lock token mismatch",
                detail=f"The cluster {cluster_name} lock token did not match",
                status=400,
            )

        self.repository.clear(lock)
        try:
            self.session.commit()
        except OperationalError as exc:
            self.session.rollback()
            raise ProblemException(
                title="Lock release failed",
                detail="Could not release cluster lock",
                status=423,
            ) from exc

        return ReleaseClusterLockResponse(cluster_name=cluster_name, message="Cluster successfully unlocked")

    @staticmethod
    def _current_time() -> datetime:
        return datetime.now(UTC).replace(tzinfo=None)

    @staticmethod
    def _is_lock_active(lock: ClusterLock, now: datetime) -> bool:
        return lock.locked and now < lock.timeout_at
