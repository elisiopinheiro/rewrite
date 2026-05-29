"""Shared FastAPI dependency providers for both apps."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import validate_m4w_credentials, validate_partner_credentials
from app.repositories.cluster import ClusterRepository
from app.repositories.feature import FeatureRepository
from app.repositories.lock import LockRepository
from app.repositories.operation import OperationRepository
from app.repositories.release import ReleaseRepository
from app.services.clusters import ClusterMapper, ClusterService, ClusterTranslator
from app.services.feature import FeatureService
from app.services.lock import ClusterLockService
from app.services.operation import OperationService
from app.services.release import ReleaseService

DbSession = Annotated[Session, Depends(get_db)]
M4WUser = Annotated[str, Depends(validate_m4w_credentials)]
PartnerUser = Annotated[str, Depends(validate_partner_credentials)]


def _get_cluster_service(
    session: DbSession,
) -> ClusterService:
    return ClusterService(
        repository=ClusterRepository(session),
        feature_repository=FeatureRepository(session),
        release_repository=ReleaseRepository(session),
        session=session,
        mapper=ClusterMapper(),
        translator=ClusterTranslator(),
    )


def _get_lock_service(session: DbSession) -> ClusterLockService:
    return ClusterLockService(
        repository=LockRepository(session),
        cluster_repository=ClusterRepository(session),
        session=session,
    )


def _get_operation_service(session: DbSession) -> OperationService:
    return OperationService(
        repository=OperationRepository(session),
        cluster_repository=ClusterRepository(session),
        session=session,
    )


def _get_release_service(session: DbSession) -> ReleaseService:
    return ReleaseService(
        repository=ReleaseRepository(session),
        feature_repository=FeatureRepository(session),
        session=session,
    )


def _get_feature_service(session: DbSession) -> FeatureService:
    return FeatureService(repository=FeatureRepository(session), session=session)


ClusterSvc = Annotated[ClusterService, Depends(_get_cluster_service)]
LockSvc = Annotated[ClusterLockService, Depends(_get_lock_service)]
OperationSvc = Annotated[OperationService, Depends(_get_operation_service)]
ReleaseSvc = Annotated[ReleaseService, Depends(_get_release_service)]
FeatureSvc = Annotated[FeatureService, Depends(_get_feature_service)]
