"""Feature API routes."""

from fastapi import APIRouter, status

from app.deps import FeatureSvc, M4WUser
from app.schemas.features import (
    FeatureCreate,
    FeatureDeleteResponse,
    FeatureListResponse,
    FeatureRead,
)

router = APIRouter(prefix="/features", tags=["features"])


@router.get("", response_model=FeatureListResponse)
def list_features(
    _user: M4WUser,
    service: FeatureSvc,
) -> FeatureListResponse:
    return service.list_features()


@router.post("", response_model=FeatureRead, status_code=status.HTTP_201_CREATED)
def create_feature(
    _user: M4WUser,
    service: FeatureSvc,
    request: FeatureCreate,
) -> FeatureRead:
    return service.create_feature(request)


@router.delete("/{feature_id}", response_model=FeatureDeleteResponse, status_code=status.HTTP_200_OK)
def delete_feature(
    feature_id: int,
    _user: M4WUser,
    service: FeatureSvc,
) -> FeatureDeleteResponse:
    return service.delete_feature(feature_id)
