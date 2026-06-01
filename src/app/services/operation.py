"""Operation application service."""

from sqlalchemy.orm import Session

from app.models.operation import Operation
from app.repositories.cluster import ClusterRepository
from app.repositories.operation import OperationRepository
from app.schemas.operations import OperationCreate, OperationListQuery, OperationListResponse, OperationRead
from app.services.errors import ProblemException


class OperationService:
    def __init__(
        self, repository: OperationRepository, cluster_repository: ClusterRepository, session: Session
    ) -> None:
        self.repository = repository
        self.cluster_repository = cluster_repository
        self.session = session

    def list_operations(self, query: OperationListQuery) -> OperationListResponse:
        operations = self.repository.list_operations(
            operation_type=query.operation_type,
            status=query.status,
            cicd_url=str(query.cicd_url) if query.cicd_url is not None else None,
            cluster_repository=query.cluster_repository,
        )
        items = [self._to_read_model(op) for op in operations]
        return OperationListResponse(count=len(items), items=items)

    def list_cluster_operations(self, cluster_name: str) -> OperationListResponse:
        cluster = self.cluster_repository.get_by_name(cluster_name)
        if cluster is None:
            raise ProblemException(title="Cluster not found", detail=f"Cluster '{cluster_name}' not found", status=404)
        operations = self.repository.list_by_cluster_id(cluster.id)
        items = [self._to_read_model(op) for op in operations]
        return OperationListResponse(count=len(items), items=items)

    def create_operation(self, cluster_name: str, request: OperationCreate) -> OperationRead:
        cluster = self.cluster_repository.get_by_name(cluster_name)
        if cluster is None:
            raise ProblemException(title="Cluster not found", detail=f"Cluster '{cluster_name}' not found", status=404)

        operation = self.repository.add_from_data(
            cluster_id=cluster.id,
            operation_type=request.operation_type,
            status=request.status,
            cicd_url=str(request.cicd_url),
            timestamp=request.timestamp,
            cluster_repository=request.cluster_repository,
        )
        self.session.commit()
        self.session.refresh(operation)
        return self._to_read_model(operation)

    @staticmethod
    def _to_read_model(operation: Operation) -> OperationRead:
        return OperationRead.model_validate(operation)
