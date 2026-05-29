from typing import Any

from fastapi import Depends
from sqlalchemy import asc
from sqlmodel import Session

from api.shared.database import get_db
from api.shared.models.clusters import Feature


class FeatureRepository:
    session: Session

    def __init__(self, session: Session = Depends(get_db)):
        self.session = session

    def get_features(self, **filters: Any) -> list[Feature]:
        json_fields = [name for name, column in Feature.__table__.columns.items() if str(column.type) == "JSON"]
        sql_filters = {}
        python_filters = {}

        for key, value in filters.items():
            if key in json_fields:
                python_filters[key] = value
            else:
                sql_filters[key] = value

        query = self.session.query(Feature).filter_by(**sql_filters).order_by(asc(Feature.id))
        features = query.all()

        if python_filters:
            features = [
                feature
                for feature in features
                if all(getattr(feature, key) == value for key, value in python_filters.items())
            ]

        return features

    def get_feature(self, id: int) -> Feature:
        return self.session.get(Feature, id)

    def save_feature(self, feature: Feature) -> Feature:
        self.session.add(feature)
        self.session.commit()
        self.session.refresh(feature)
        return feature

    def delete_feature(self, feature: Feature) -> dict:
        self.session.delete(feature)
        self.session.commit()
        return {"msg": f"Feature {feature.name} deleted successfully"}
