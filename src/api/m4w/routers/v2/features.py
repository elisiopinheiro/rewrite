"""Features v2 router methods"""

from typing import List

from fastapi import APIRouter, Depends

from api.m4w.auth import validate_credentials
from api.shared.logger import logger
from api.shared.models.features import Feature
from api.shared.repository.feature_repository import FeatureRepository

router = APIRouter(prefix="/v2/features", tags=["Features v2"])


@router.get(
    "",
    response_model=List[Feature],
)
def get_features_v2(
    username: str = Depends(validate_credentials),
    feature_repository: FeatureRepository = Depends(FeatureRepository),
) -> List[Feature]:
    """
    \f Get all features

    Args:
        username (str, optional): Username. Defaults to Depends(validate_credentials).
        feature_repository (FeatureRepository, optional): Feature repository. Defaults to Depends(FeatureRepository).

    Returns:
        List[Feature]: List of features
    """
    logger.info("Received GET /v2/features request")
    features = feature_repository.get_features()

    return features
