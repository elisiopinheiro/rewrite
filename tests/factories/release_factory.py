from typing import Dict

import factory
from factory.alchemy import SQLAlchemyModelFactory
from factory.fuzzy import FuzzyChoice
from faker import Faker

from api.shared.enums import Provider
from api.shared.models.releases import Release

fake = Faker()


class ReleaseFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Release
        sqlalchemy_session_persistence = "commit"

    name = factory.Sequence(lambda n: f"test-release-{n}")
    provider = FuzzyChoice(Provider)
    reserved_namespaces = factory.LazyFunction(lambda: [f"reserved-{fake.word()}", f"system-{fake.word()}"])


def make_add_release_payload(provider: Provider = None, **overrides) -> Dict:
    """Create release test data.

    Args:
        provider: Must be Provider.AWS or Provider.AZURE.
                 If not provided, defaults to Provider.AWS.
        overrides: Optional dictionary of values to override the default release data.

    Returns:
        Release data.

    Raises:
        ValueError: If provider is not Provider.AWS or Provider.AZURE.
    """
    if provider is None:
        provider = Provider.AWS

    if provider not in [Provider.AWS, Provider.AZURE]:
        raise ValueError(f"Provider must be Provider.AWS or Provider.AZURE, got {provider}")

    base_data = {
        "name": f"test-release-{fake.uuid4()}",
        "provider": provider.value,
        "reserved_namespaces": [f"reserved-{fake.word()}", f"system-{fake.word()}"],
        "features": [],
    }

    if overrides:
        base_data.update(overrides)

    return base_data


def make_release_with_features_payload(provider: Provider = None, **overrides) -> Dict:
    """Create release test data with features.

    Args:
        provider: Must be Provider.AWS or Provider.AZURE.
                 If not provided, defaults to Provider.AWS.
        overrides: Optional dictionary of values to override the default release data.

    Returns:
        Dict containing the release data with features.

    Raises:
        ValueError: If provider is not Provider.AWS or Provider.AZURE.
    """
    if provider is None:
        provider = Provider.AWS

    if provider not in [Provider.AWS, Provider.AZURE]:
        raise ValueError(f"Provider must be Provider.AWS or Provider.AZURE, got {provider}")

    base_data = make_add_release_payload(provider, **overrides)

    # Add some test features
    base_data["features"] = [
        {
            "name": f"test-feature-{fake.word()}",
            "type": "core",
            "dependencies": [f"dep-{fake.word()}"],
            "constraints": [],
        },
        {"name": f"test-feature-{fake.word()}", "type": "optional", "dependencies": [], "constraints": []},
    ]

    if overrides:
        base_data.update(overrides)

    return base_data
