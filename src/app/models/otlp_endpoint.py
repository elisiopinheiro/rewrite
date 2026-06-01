"""Client OTLP endpoint table model."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.cluster import Cluster


class ClientOTLPEndpoint(Base):
    __tablename__ = "clientotlpendpoint"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    type: Mapped[str]
    endpoint: Mapped[str]
    signals: Mapped[list[str]] = mapped_column(JSON)
    auth: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    config: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    cluster_id: Mapped[int] = mapped_column(ForeignKey("cluster.id", ondelete="CASCADE"), index=True)

    cluster: Mapped[Cluster] = relationship(back_populates="client_otlp_endpoints")
