"""Feature application service."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.feature import Feature
from app.repositories.feature import FeatureRepository
from app.schemas.features import FeatureCreate, FeatureDeleteResponse, FeatureListResponse, FeatureRead
from app.services.errors import ProblemException


class FeatureService:
    def __init__(self, repository: FeatureRepository, session: Session) -> None:
        self.repository = repository
        self.session = session

    def list_features(self) -> FeatureListResponse:
        features = self.repository.list_features()
        items = [self._to_read_model(feature) for feature in features]
        return FeatureListResponse(count=len(items), items=items)

    def create_feature(self, request: FeatureCreate) -> FeatureRead:
        try:
            feature = self.repository.add_from_data(request.model_dump())
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ProblemException(title="Feature already exists", detail="Feature already exists", status=409) from exc
        self.session.refresh(feature)
        return self._to_read_model(feature)

    def delete_feature(self, feature_id: int) -> FeatureDeleteResponse:
        feature = self.repository.get(feature_id)
        if feature is None:
            raise ProblemException(title="Feature not found", detail="Feature not found", status=404)
        name = feature.name
        self.repository.delete(feature)
        self.session.commit()
        return FeatureDeleteResponse(message=f"Feature {name} deleted successfully")

    @staticmethod
    def _to_read_model(feature: Feature) -> FeatureRead:
        return FeatureRead.model_validate(feature)
