from typing import Any

import sqlalchemy
from fastapi import Depends
from sqlalchemy import asc
from sqlmodel import Session

from api.shared.database import get_db
from api.shared.models.operation import Operation


class OperationRepository:
    session: Session

    def __init__(self, session: Session = Depends(get_db)):
        self.session = session

    def get_cluster_operations(self, cluster_id: int) -> list[Operation]:
        statement = sqlalchemy.select(Operation).where(Operation.cluster_id == cluster_id).order_by(asc(Operation.id))
        result = self.session.execute(statement)
        operations = result.scalars().all()
        return operations

    def get_operations(self, **filters: Any) -> list[Operation]:
        query = self.session.query(Operation).filter_by(**filters).order_by(asc(Operation.id))
        operations = query.all()
        return operations

    def save_operation(self, operation: Operation) -> Operation:
        self.session.add(operation)
        self.session.commit()
        self.session.refresh(operation)
        return operation
