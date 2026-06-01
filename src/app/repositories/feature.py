"""Feature repository — data access for features."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sqlalchemy import asc, select
from sqlalchemy.orm import Session

from app.models.feature import Feature


class FeatureRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_features(self, **filters: Any) -> list[Feature]:
        statement = select(Feature).filter_by(**filters).order_by(asc(Feature.id))
        return list(self.session.scalars(statement).all())

    def get(self, feature_id: int) -> Feature | None:
        return self.session.get(Feature, feature_id)

    def add(self, feature: Feature) -> Feature:
        self.session.add(feature)
        return feature

    def add_from_data(self, data: Mapping[str, Any]) -> Feature:
        persisted_data = self._to_persisted_data(data)
        return self.add(Feature(**persisted_data))

    def resolve(self, data: Mapping[str, Any]) -> Feature:
        """Find an existing feature matching the data, or return a new unsaved instance."""
        persisted_data = self._to_persisted_data(data)
        candidates = self.list_features(name=persisted_data.get("name"))
        for candidate in candidates:
            candidate_data = self._normalize_persisted_data({key: getattr(candidate, key) for key in persisted_data})
            if candidate_data == persisted_data:
                return candidate
        return Feature(**persisted_data)

    def delete(self, feature: Feature) -> None:
        self.session.delete(feature)

    @staticmethod
    def _to_persisted_data(data: Mapping[str, Any]) -> dict[str, Any]:
        persisted_data = {("type" if key == "feature_type" else key): value for key, value in data.items()}
        return FeatureRepository._normalize_persisted_data(persisted_data)

    @staticmethod
    def _normalize_persisted_data(data: Mapping[str, Any]) -> dict[str, Any]:
        normalized_data = dict(data)
        if normalized_data.get("dependencies") is None:
            normalized_data["dependencies"] = []
        if normalized_data.get("constraints") is None:
            normalized_data["constraints"] = []
        if normalized_data.get("namespaced") is None:
            normalized_data["namespaced"] = False
        return normalized_data
