"""Releases router methods"""

from typing import List, Union

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from sqlalchemy.exc import IntegrityError

from api.m4w.auth import validate_credentials
from api.shared.enums import Provider
from api.shared.logger import logger
from api.shared.models.httperror import HTTPError
from api.shared.models.releases import (
    OrderByReleaseFields,
    ReleaseRequest,
    ReleaseResponse,
    ReleaseUpdateRequest,
)
from api.shared.repository.release_repository import ReleaseRepository

router = APIRouter(prefix="/v1/releases")


@router.post("", responses={409: {"model": HTTPError}}, tags=["Releases v1"], response_model=ReleaseResponse)
def add_release(
    release_request: ReleaseRequest,
    username: str = Depends(validate_credentials),
    release_repository: ReleaseRepository = Depends(ReleaseRepository),
) -> ReleaseResponse:
    """
    \f Add a new release

    Args:
        release_request (ReleaseRequest): Release request payload
        username (str, optional): Username. Defaults to Depends(validate_credentials).
        release_repository (ReleaseRepository, optional): Release repository. Defaults to Depends(ReleaseRepository).

    Raises:
        HTTPException: HTTP_409_CONFLICT if release already exists

    Returns:
        ReleaseResponse: Created release
    """
    logger.info("Received POST /v1/releases request - body: %s", release_request.model_dump())
    try:
        return release_repository.add_release(release_request=release_request)
    except IntegrityError as e:
        logger.exception("")
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Release already exists",
        ) from e


@router.get(
    "",
    response_model=List[ReleaseResponse],
    responses={404: {"model": HTTPError}},
    tags=["Releases v1"],
)
def get_releases(
    order_by: Union[OrderByReleaseFields, None] = "id",
    name: Union[str, None] = None,
    provider: Union[Provider, None] = None,
    username: str = Depends(validate_credentials),
    release_repository: ReleaseRepository = Depends(ReleaseRepository),
) -> List[ReleaseResponse]:
    """
    \f Get releases with optional filters

    Args:
        order_by (Union[OrderByReleaseFields, None], optional): Order by field. Defaults to "id".
        name (Union[str, None], optional): Release name. Defaults to None.
        provider (Union[Provider, None], optional): Provider filter. Defaults to None.
        username (str, optional): Username. Defaults to Depends(validate_credentials).
        release_repository (ReleaseRepository, optional): Release repository. Defaults to Depends(ReleaseRepository).

    Raises:
        HTTPException: HTTP_404_NOT_FOUND if no releases match the filters
        HTTPValidationError: HTTP_422_UNPROCESSABLE_ENTITY if order_by value is not one of the allowed fields

    Returns:
        List[ReleaseResponse]: List of releases
    """
    logger.info("Received GET /v1/releases request - name: %s, provider: %s, order_by: %s", name, provider, order_by)
    args = locals()
    args.pop("username")
    args.pop("order_by")
    args.pop("release_repository")
    parsed_args = {k: v for k, v in args.items() if v is not None}
    releases = release_repository.get_releases(order_by, **parsed_args)

    parsed_releases = [ReleaseResponse.parse_release(release) for release in releases]

    if not parsed_releases:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="No releases found",
        )

    return parsed_releases


@router.get(
    "/{provider}/{name:path}",
    response_model=ReleaseResponse,
    responses={404: {"model": HTTPError}},
    tags=["Releases v1"],
)
def get_release(
    name: str,
    provider: Provider,
    username: str = Depends(validate_credentials),
    release_repository: ReleaseRepository = Depends(ReleaseRepository),
) -> ReleaseResponse:
    """
    \f Get release by provider and name

    Args:
        name (str): Release name
        provider (Provider): Provider
        username (str, optional): Username. Defaults to Depends(validate_credentials).
        release_repository (ReleaseRepository, optional): Release repository. Defaults to Depends(ReleaseRepository).

    Raises:
        HTTPException: HTTP_404_NOT_FOUND if release does not exist

    Returns:
        ReleaseResponse: Release data
    """
    logger.info("Received GET /v1/releases/%s/%s request", provider, name)
    args = locals()
    args.pop("username")
    args.pop("release_repository")
    parsed_args = {k: v for k, v in args.items() if v is not None}
    releases = release_repository.get_releases(**parsed_args)

    if not releases:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Release not found",
        )

    return ReleaseResponse.parse_release(release=releases[0])


@router.delete("/{id}", responses={404: {"model": HTTPError}}, tags=["Releases v1"], response_model=None)
def delete_release(
    id: int,
    username: str = Depends(validate_credentials),
    release_repository: ReleaseRepository = Depends(ReleaseRepository),
) -> None:
    """
    \f Delete release by ID

    Args:
        id (int): Release ID
        username (str, optional): Username. Defaults to Depends(validate_credentials).
        release_repository (ReleaseRepository, optional): Release repository. Defaults to Depends(ReleaseRepository).

    Raises:
        HTTPException: HTTP_404_NOT_FOUND if release does not exist

    Returns:
        dict: Deletion confirmation
    """
    logger.info("Received DELETE /v1/releases/%s request", id)
    release = release_repository.get_release(id)
    if release is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Release not found",
        )
    return release_repository.delete_release(release)


@router.patch(
    "/{id}",
    response_model=ReleaseResponse,
    responses={404: {"model": HTTPError}},
    tags=["Releases v1"],
)
def update_release(
    id: int,
    release_update: ReleaseUpdateRequest,
    username: str = Depends(validate_credentials),
    release_repository: ReleaseRepository = Depends(ReleaseRepository),
) -> ReleaseResponse:
    """
    \f Update a release by ID

    Args:
        id (int): Release ID
        release_update (ReleaseUpdateRequest): Fields to update
        username (str, optional): Username. Defaults to Depends(validate_credentials).
        release_repository (ReleaseRepository, optional): Release repository. Defaults to Depends(ReleaseRepository).

    Raises:
        HTTPException: HTTP_404_NOT_FOUND if release does not exist

    Returns:
        ReleaseResponse: Updated release
    """
    logger.info("Received PATCH /v1/releases/%s request - body: %s", id, release_update.model_dump())
    release = release_repository.get_release(id)

    if not release:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Release with id {id} not found",
        )

    return release_repository.update_release(release, release_update)
