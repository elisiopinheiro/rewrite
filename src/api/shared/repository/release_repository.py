from typing import Any

from fastapi import Depends
from sqlalchemy import asc
from sqlmodel import Session, select

from api.shared.database import get_db
from api.shared.models.features import Feature
from api.shared.models.releases import (
    Release,
    ReleaseFeature,
    ReleaseRequest,
    ReleaseResponse,
)
from api.shared.repository.feature_repository import FeatureRepository


class ReleaseRepository:
    session: Session
    feature_repository: FeatureRepository

    def __init__(
        self, session: Session = Depends(get_db), feature_repository: FeatureRepository = Depends(FeatureRepository)
    ):
        self.session = session
        self.feature_repository = feature_repository

    def add_release(self, release_request: ReleaseRequest) -> ReleaseResponse:
        release = Release.model_validate(
            release_request,
            update={"features": []},
        )

        if release_request.features:
            for release_feature in release_request.features:
                db_features = self.feature_repository.get_features(
                    name=release_feature.name,
                    type=release_feature.type,
                    namespaced=release_feature.namespaced,
                    constraints=release_feature.constraints,
                )
                feature = next(
                    (db_feature for db_feature in db_features if db_feature == release_feature),
                    Feature.model_validate(release_feature.model_dump()),
                )

                release.features.append(ReleaseFeature(release=release, feature=feature))

        db_release = self.save_release(release)
        return ReleaseResponse.parse_release(db_release)

    def save_release(self, release: Release) -> Release:
        self.session.add(release)
        self.session.commit()
        self.session.refresh(release)
        return release

    def get_releases(self, order_by="id", **filters: Any) -> list[Release]:
        statement = select(Release).filter_by(**filters).order_by(asc(getattr(Release, order_by)))
        releases = self.session.execute(statement).unique().scalars().all()
        return releases

    def get_release(self, id: int) -> Release:
        return self.session.get(Release, id)

    def delete_release(self, release: Release) -> dict:
        self.session.delete(release)
        self.session.commit()
        return {"msg": f"Release {release.name} deleted successfully"}
