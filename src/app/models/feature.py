"""Feature table model."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.cluster import ClusterFeature
    from app.models.release import ReleaseFeature


class Feature(Base):
    __tablename__ = "feature"
    __table_args__ = (UniqueConstraint("name", name="feature_name_uc"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    type: Mapped[str] = mapped_column(default="optional")
    dependencies: Mapped[list[str] | None] = mapped_column(JSON)
    constraints: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, default=list, server_default=text("'[]'"))
    namespaced: Mapped[bool] = mapped_column(default=False, server_default=text("false"))

    cluster_features: Mapped[list[ClusterFeature]] = relationship(back_populates="feature")
    release_features: Mapped[list[ReleaseFeature]] = relationship(back_populates="feature")
