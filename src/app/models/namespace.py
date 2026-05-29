"""Client namespace table model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ARRAY, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.cluster import Cluster


class ClientNamespace(Base):
    __tablename__ = "clientnamespace"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    consumed_by: Mapped[str | None] = mapped_column(nullable=True)
    admin: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    viewer: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    editor: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    cluster_id: Mapped[int] = mapped_column(ForeignKey("cluster.id", ondelete="CASCADE"), index=True)

    cluster: Mapped[Cluster] = relationship(back_populates="client_namespaces")
