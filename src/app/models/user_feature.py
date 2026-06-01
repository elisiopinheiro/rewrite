"""User feature table model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.cluster import Cluster


class UserFeature(Base):
    __tablename__ = "userfeature"

    name: Mapped[str] = mapped_column(primary_key=True)
    cluster_id: Mapped[int] = mapped_column(ForeignKey("cluster.id", ondelete="CASCADE"), primary_key=True)
    namespace: Mapped[str]
    repo_url: Mapped[str]
    commit_hash: Mapped[str]
    helm_path: Mapped[str | None]
    values_path: Mapped[str | None]

    cluster: Mapped[Cluster] = relationship(back_populates="user_features")
