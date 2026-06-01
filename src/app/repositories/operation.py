"""Operation repository — data access for operations."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import asc, select
from sqlalchemy.orm import Session

from app.models.operation import Operation


class OperationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_operations(
        self,
        *,
        cluster_id: int | None = None,
        operation_type: str | None = None,
        status: str | None = None,
        cicd_url: str | None = None,
        cluster_repository: str | None = None,
    ) -> list[Operation]:
        statement = select(Operation).order_by(asc(Operation.id))
        if cluster_id is not None:
            statement = statement.where(Operation.cluster_id == cluster_id)
        if operation_type is not None:
            statement = statement.where(Operation.operation_type == operation_type)
        if status is not None:
            statement = statement.where(Operation.status == status)
        if cicd_url is not None:
            statement = statement.where(Operation.cicd_url == cicd_url)
        if cluster_repository is not None:
            statement = statement.where(Operation.cluster_repository == cluster_repository)
        return list(self.session.scalars(statement).all())

    def list_by_cluster_id(self, cluster_id: int) -> list[Operation]:
        return self.list_operations(cluster_id=cluster_id)

    def add(self, operation: Operation) -> Operation:
        self.session.add(operation)
        return operation

    def add_from_data(
        self,
        *,
        cluster_id: int,
        operation_type: str,
        status: str,
        cicd_url: str,
        timestamp: datetime | None = None,
        cluster_repository: str | None = None,
    ) -> Operation:
        return self.add(
            Operation(
                cluster_id=cluster_id,
                operation_type=operation_type,
                status=status,
                cicd_url=cicd_url,
                timestamp=timestamp,
                cluster_repository=cluster_repository,
            )
        )
