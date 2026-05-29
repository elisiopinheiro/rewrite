"""Features router methods"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from sqlalchemy.exc import IntegrityError

from api.m4w.auth import validate_credentials
from api.shared.logger import logger
from api.shared.models.features import Feature, FeatureBase
from api.shared.models.httperror import HTTPError
from api.shared.repository.feature_repository import FeatureRepository

router = APIRouter(prefix="/v1/features")


@router.post("", responses={409: {"model": HTTPError}}, response_model=Feature, tags=["Features v1"])
def add_feature(
    feature_base: FeatureBase,
    username: str = Depends(validate_credentials),
    feature_repository: FeatureRepository = Depends(FeatureRepository),
) -> Feature:
    """
    \f Add a new feature

    Args:
        feature_base (FeatureBase): Feature data
        username (str, optional): Username. Defaults to Depends(validate_credentials).
        feature_repository (FeatureRepository, optional): Feature repository. Defaults to Depends(FeatureRepository).

    Raises:
        HTTPException: HTTP_409_CONFLICT if feature already exists

    Returns:
        Feature: Created feature
    """
    logger.info("Received POST /v1/features request - body: %s", feature_base.model_dump())
    try:
        feature = Feature.model_validate(feature_base)

        return feature_repository.save_feature(feature)
    except IntegrityError as e:
        logger.exception("")
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Feature already exists",
        ) from e


@router.get(
    "",
    response_model=List[Feature],
    responses={404: {"model": HTTPError}},
    tags=["Features v1"],
)
def get_features(
    username: str = Depends(validate_credentials),
    feature_repository: FeatureRepository = Depends(FeatureRepository),
) -> List[Feature]:
    """
    \f Get all features

    Args:
        username (str, optional): Username. Defaults to Depends(validate_credentials).
        feature_repository (FeatureRepository, optional): Feature repository. Defaults to Depends(FeatureRepository).

    Raises:
        HTTPException: HTTP_404_NOT_FOUND if no features found

    Returns:
        List[Feature]: List of features
    """
    logger.info("Received GET /v1/features request")
    features = feature_repository.get_features()

    if not features:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Features not found",
        )

    return features


@router.delete("/{id}", responses={404: {"model": HTTPError}}, response_model=None, tags=["Features v1"])
def delete_feature(
    id: int,
    username: str = Depends(validate_credentials),
    feature_repository: FeatureRepository = Depends(FeatureRepository),
) -> None:
    """
    \f Delete feature by ID

    Args:
        id (int): Feature ID
        username (str, optional): Username. Defaults to Depends(validate_credentials).
        feature_repository (FeatureRepository, optional): Feature repository. Defaults to Depends(FeatureRepository).

    Raises:
        HTTPException: HTTP_404_NOT_FOUND if feature does not exist

    Returns:
        dict: Deletion confirmation
    """
    logger.info("Received DELETE /v1/features/%s request", id)
    feature = feature_repository.get_feature(id)
    if feature is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Feature not found",
        )
    return feature_repository.delete_feature(feature)
