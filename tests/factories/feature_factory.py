from factory.alchemy import SQLAlchemyModelFactory
from faker import Faker

from api.shared.models.features import Feature, FeatureBase, FeatureType

fake = Faker("en-US")


# SQL Model Factories
class FeatureFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Feature
        sqlalchemy_session_persistence = "commit"

    name = f"{fake.word()}-feature"
    type = FeatureType.OPTIONAL
    dependencies = []
    constraints = []
    namespaced = False


def make_add_feature_payload(**overrides) -> FeatureBase:
    feature = {
        "name": f"{fake.word()}-feature",
        "type": FeatureType.OPTIONAL,
        "dependencies": [],
        "constraints": [],
        "namespaced": False,
    }

    if overrides:
        feature.update(overrides)

    return FeatureBase(**feature)
