"""Release application service."""

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.release import Release
from app.repositories.feature import FeatureRepository
from app.repositories.release import ReleaseRepository
from app.schemas.features import FeatureRead
from app.schemas.releases import (
    ReleaseCreate,
    ReleaseDeleteResponse,
    ReleaseListQuery,
    ReleaseListResponse,
    ReleaseRead,
)
from app.services.errors import ProblemException


class ReleaseService:
    def __init__(self, repository: ReleaseRepository, feature_repository: FeatureRepository, session: Session) -> None:
        self.repository = repository
        self.feature_repository = feature_repository
        self.session = session

    def list_releases(self, query: ReleaseListQuery) -> ReleaseListResponse:
        releases = self.repository.list_releases(name=query.name, provider=query.provider, order_by=query.order_by)
        items = [self._to_read_model(release) for release in releases]
        return ReleaseListResponse(count=len(items), items=items)

    def get_release(self, release_id: int) -> ReleaseRead:
        release = self.repository.get(release_id)
        if release is None:
            raise ProblemException(title="Release not found", detail="Release not found", status=404)
        return self._to_read_model(release)

    def create_release(self, request: ReleaseCreate) -> ReleaseRead:
        features = [
            self.feature_repository.resolve(requested_feature.model_dump()) for requested_feature in request.features
        ]

        try:
            persisted = self.repository.add_from_data(request.model_dump(exclude={"features"}), features)
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ProblemException(title="Release already exists", detail="Release already exists", status=409) from exc
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise ProblemException(
                title="Internal Server Error", detail="A database error occurred.", status=500
            ) from exc

        stored = self.repository.get(persisted.id)
        if stored is None:
            stored = persisted
        return self._to_read_model(stored)

    def delete_release(self, release_id: int) -> ReleaseDeleteResponse:
        release = self.repository.get(release_id)
        if release is None:
            raise ProblemException(title="Release not found", detail="Release not found", status=404)
        name = release.name
        try:
            self.repository.delete(release)
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ProblemException(
                title="Release delete conflict", detail="Release could not be deleted", status=409
            ) from exc
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise ProblemException(
                title="Internal Server Error", detail="A database error occurred.", status=500
            ) from exc
        return ReleaseDeleteResponse(message=f"Release {name} deleted successfully")

    @staticmethod
    def _to_read_model(release: Release) -> ReleaseRead:
        return ReleaseRead(
            id=release.id,
            name=release.name,
            provider=release.provider,
            reserved_namespaces=release.reserved_namespaces or [],
            features=[FeatureRead.model_validate(feature_link.feature) for feature_link in release.features],
        )
