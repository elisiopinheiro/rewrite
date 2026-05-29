"""Release repository — data access for releases."""

from __future__ import annotations

import builtins
from collections.abc import Mapping
from typing import Any

from sqlalchemy import asc, select
from sqlalchemy.orm import Session, selectinload

from app.models.feature import Feature
from app.models.release import Release, ReleaseFeature
from app.schemas.enums import ReleaseOrderBy

_RELEASE_LOAD_OPTIONS: tuple[Any, ...] = (
    selectinload(Release.features).selectinload(ReleaseFeature.feature),
)

_RELEASE_ORDER_COLUMNS: Mapping[ReleaseOrderBy, Any] = {
    ReleaseOrderBy.ID: Release.id,
    ReleaseOrderBy.NAME: Release.name,
}


class ReleaseRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(
        self,
        *,
        name: str | None = None,
        provider: str | None = None,
        order_by: ReleaseOrderBy = ReleaseOrderBy.ID,
    ) -> builtins.list[Release]:
        statement = self._base_statement()
        if name is not None:
            statement = statement.where(Release.name == name)
        if provider is not None:
            statement = statement.where(Release.provider == provider)
        statement = statement.order_by(asc(_RELEASE_ORDER_COLUMNS[order_by]))
        return list(self.session.scalars(statement).all())

    def list_by_name_and_provider(self, *, name: str, provider: str) -> builtins.list[Release]:
        statement = self._base_statement().where(Release.name == name, Release.provider == provider).order_by(asc(Release.id))
        return list(self.session.scalars(statement).all())

    def exists_by_name_and_provider(self, *, name: str, provider: str) -> bool:
        statement = select(Release.id).where(Release.name == name, Release.provider == provider)
        return self.session.scalar(statement) is not None

    def get(self, release_id: int) -> Release | None:
        statement = self._base_statement().where(Release.id == release_id)
        return self.session.scalars(statement).one_or_none()

    def add(self, release: Release) -> Release:
        self.session.add(release)
        return release

    def add_from_data(self, data: dict[str, Any], features: builtins.list[Feature]) -> Release:
        release = Release(**data, features=[])
        for feature in features:
            release.features.append(ReleaseFeature(release=release, feature=feature))
        return self.add(release)

    def delete(self, release: Release) -> None:
        self.session.delete(release)

    @staticmethod
    def _base_statement() -> Any:
        return select(Release).options(*_RELEASE_LOAD_OPTIONS)
