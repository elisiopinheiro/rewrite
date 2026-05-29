"""Operation table model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.cluster import Cluster


class Operation(Base):
    __tablename__ = "operation"

    id: Mapped[int] = mapped_column(primary_key=True)
    operation_type: Mapped[str] = mapped_column("type", nullable=False)
    status: Mapped[str] = mapped_column(nullable=False)
    cicd_url: Mapped[str] = mapped_column(nullable=False)
    timestamp: Mapped[datetime | None] = mapped_column(nullable=True)
    cluster_repository: Mapped[str | None] = mapped_column(nullable=True)
    cluster_id: Mapped[int | None] = mapped_column(ForeignKey("cluster.id", ondelete="SET NULL"), index=True, nullable=True)

    cluster: Mapped[Cluster | None] = relationship(back_populates="operations")
