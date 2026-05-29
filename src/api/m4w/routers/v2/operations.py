"""Operations v2 router methods"""

from typing import List, Union

from fastapi import APIRouter, Depends

from api.m4w.auth import validate_credentials
from api.shared.logger import logger
from api.shared.models.operation import Operation
from api.shared.repository.operation_repository import OperationRepository

router = APIRouter(prefix="/v2/operations", tags=["Operations v2"])


@router.get(
    "",
    response_model=List[Operation],
)
def get_operations_v2(
    type: Union[str, None] = None,
    status: Union[str, None] = None,
    cicd_url: Union[str, None] = None,
    cluster_repository: Union[str, None] = None,
    username: str = Depends(validate_credentials),
    operation_repository: OperationRepository = Depends(OperationRepository),
) -> List[Operation]:
    """
    \f Get operations with optional filters

    Args:
        type (Union[str, None], optional): Operation type. Defaults to None.
        status (Union[str, None], optional): Operation status. Defaults to None.
        cicd_url (Union[str, None], optional): CICD URL. Defaults to None.
        cluster_repository (Union[str, None], optional): Cluster repository. Defaults to None.
        username (str, optional): Username. Defaults to Depends(validate_credentials).
        operation_repository (OperationRepository, optional): Operation repository.
        Defaults to Depends(OperationRepository).

    Returns:
        List[Operation]: List of operations
    """
    args = locals()
    args.pop("username")
    args.pop("operation_repository")
    parsed_args = {k: v for k, v in args.items() if v}
    logger.info("Received GET /v2/operations request - filters: %s", parsed_args)
    operations = operation_repository.get_operations(**parsed_args)

    return operations
