"""Release table model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.feature import Feature


class Release(Base):
    __tablename__ = "release"
    __table_args__ = (UniqueConstraint("name", "provider", name="release_name_provider_uc"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    provider: Mapped[str]
    reserved_namespaces: Mapped[list[str]] = mapped_column(JSON, default=list)

    features: Mapped[list[ReleaseFeature]] = relationship(back_populates="release", cascade="all, delete-orphan")


class ReleaseFeature(Base):
    """Association table between releases and features."""

    __tablename__ = "releasefeature"

    release_id: Mapped[int] = mapped_column(ForeignKey("release.id", ondelete="CASCADE"), primary_key=True)
    feature_id: Mapped[int] = mapped_column(ForeignKey("feature.id", ondelete="CASCADE"), primary_key=True)

    release: Mapped[Release] = relationship(back_populates="features")
    feature: Mapped[Feature] = relationship(back_populates="release_features")
