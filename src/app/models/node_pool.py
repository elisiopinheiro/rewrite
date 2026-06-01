"""Additional node pool table model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.cluster import Cluster


class AdditionalNodePool(Base):
    __tablename__ = "additionalnodepool"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    node_min_count: Mapped[int]
    node_max_count: Mapped[int]
    tshirt_size: Mapped[str]
    cluster_id: Mapped[int] = mapped_column(ForeignKey("cluster.id", ondelete="CASCADE"), index=True)

    cluster: Mapped[Cluster] = relationship(back_populates="additional_node_pools")
