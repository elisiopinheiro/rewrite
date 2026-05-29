import factory
from factory.alchemy import SQLAlchemyModelFactory
from faker import Faker

from api.shared.models.storage_classes import AzureStorageClassSKU, StorageClass, StorageClassPayload, StorageClassType

fake = Faker("en-US")


# SQL Model Factories
class RemoteStorageClassFactory(SQLAlchemyModelFactory):
    class Meta:
        model = StorageClass
        sqlalchemy_session_persistence = "commit"

    type = StorageClassType.AZ_CABS
    name = factory.Faker("slug")
    config = factory.LazyAttribute(
        lambda _: {
            "subscription_id": fake.uuid4(),
            "storage_account": f"rg-{fake.word()}",
            "resource_group": f"storage{fake.lexify(text='????????')}",
            "sku_name": fake.random_element(elements=list(AzureStorageClassSKU)),
            "container": fake.random_element(elements=[None, fake.slug()]),
        }
    )


class UltraSSDStorageClassFactory(SQLAlchemyModelFactory):
    class Meta:
        model = StorageClass
        sqlalchemy_session_persistence = "commit"

    type = StorageClassType.AZ_USSD
    name = factory.Faker("slug")
    config = factory.LazyAttribute(
        lambda _: {
            "iops": fake.random_int(min=1200, max=40000),
            "throughput": fake.random_int(min=300, max=10000),
        }
    )


def make_add_remote_storage_class_payload(name=None, **overrides) -> StorageClassPayload:
    """Create a StorageClassPayload payload with remote storage classes for testing.

    Args:
        **overrides: Optional dictionary of values to override the default data.

    Returns:
        StorageClassPayload: A payload instance for creating remote storage classes.

    Examples:
        # Create a default payload
        payload = make_add_remote_storage_class_payload()

        # Create with custom values
        payload = make_add_remote_storage_class_payload(
            name="my-storage-class",
            cloudroom_id="abc-123",
            tier=AzureSku.STANDARD_LRS
        )
    """
    name = name or fake.slug()
    config = {
        "subscription_id": fake.uuid4(),
        "resource_group": f"rg-{fake.word()}",
        "storage_account": f"storage{fake.lexify(text='????????')}",
        "sku_name": fake.random_element(elements=list(AzureStorageClassSKU)),
        "container": fake.random_element(elements=[None, fake.slug()]),
    }

    # Update config with any field overrides
    if overrides:
        config.update(overrides)

    return {"remote": {name: config}}


def make_add_ultra_ssd_storage_class_payload(name=None, **overrides) -> StorageClassPayload:
    """Create a StorageClassPayload payload with ultra ssd storage classes for testing.
    Args:
        **overrides: Optional dictionary of values to override the default data.
    Returns:
        StorageClassPayload: A payload instance for creating ultra ssd storage classes.
    Examples:
        # Create a default payload
        payload = make_add_ultra_ssd_storage_class_payload()
        # Create with custom values
        payload = make_add_ultra_ssd_storage_class_payload(
            name="my-ultra-ssd-storage-class",
            iops=1200,
            throughput=300
        )
    """
    name = name or fake.slug()
    config = {
        "iops": fake.random_int(min=1200, max=40000),
        "throughput": fake.random_int(min=300, max=10000),
    }

    # Update config with any field overrides
    if overrides:
        config.update(overrides)

    return {"ultra_ssd": {name: config}}
