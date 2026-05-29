"""Cluster lock table model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.cluster import Cluster


class ClusterLock(Base):
    __tablename__ = "clusterlock"

    cluster_id: Mapped[int] = mapped_column(ForeignKey("cluster.id", ondelete="CASCADE"), primary_key=True)
    locked: Mapped[bool] = mapped_column(nullable=False)
    owner: Mapped[str | None] = mapped_column(nullable=True)
    token: Mapped[str | None] = mapped_column(nullable=True)
    timeout_at: Mapped[datetime] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)

    cluster: Mapped[Cluster] = relationship(back_populates="cluster_lock")
