"""Releases v2 router methods"""

from typing import List, Union

from fastapi import APIRouter, Depends

from api.m4w.auth import validate_credentials
from api.shared.enums import Provider
from api.shared.logger import logger
from api.shared.models.releases import (
    OrderByReleaseFields,
    ReleaseResponse,
)
from api.shared.repository.release_repository import ReleaseRepository

router = APIRouter(prefix="/v2")


@router.get(
    "/releases",
    response_model=List[ReleaseResponse],
    tags=["Releases v2"],
)
def get_releases_v2(
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

    Returns:
        List[ReleaseResponse]: List of releases

    Raises:
        HTTPValidationError: HTTP_422_UNPROCESSABLE_ENTITY if order_by value is not one of the allowed fields
    """
    logger.info("Received GET /v2/releases request - name: %s, provider: %s, order_by: %s", name, provider, order_by)
    args = locals()
    args.pop("username")
    args.pop("order_by")
    args.pop("release_repository")
    parsed_args = {k: v for k, v in args.items() if v is not None}
    releases = release_repository.get_releases(order_by, **parsed_args)

    parsed_releases = [ReleaseResponse.parse_release(release) for release in releases]

    return parsed_releases
