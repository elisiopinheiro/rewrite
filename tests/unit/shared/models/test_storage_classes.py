import pytest
from pydantic import ValidationError

from api.shared.models.storage_classes import (
    AzureCrossAccountBlobStorage,
    AzureStorageClassSKU,
    AzureUltraSSDStorageClass,
    StorageClass,
    StorageClassBase,
    StorageClassPayload,
    StorageClassType,
)


@pytest.mark.unit
@pytest.mark.models
@pytest.mark.storage_classes
class TestStorageClasses:
    """Unit tests for StorageClasses model - focuses on from_list/to_list conversions."""

    def test_from_list_and_to_list_mixed_types(self):
        """Test from_list and to_list methods with mixed storage class types."""
        # Create DB objects with both types
        db_objects = [
            StorageClass(
                id=1,
                cluster_id=1,
                type=StorageClassType.AZ_CABS,
                name="remote-1",
                config={
                    "subscription_id": "12345678-1234-1234-1234-123456789012",
                    "storage_account": "storage123",
                    "resource_group": "rg-prod",
                    "sku_name": AzureStorageClassSKU.STANDARD_LRS,
                },
            ),
            StorageClass(
                id=2,
                cluster_id=1,
                type=StorageClassType.AZ_USSD,
                name="ultra-1",
                config={"iops": 5000, "throughput": 500},
            ),
        ]

        # Test from_list
        storage_classes = StorageClassPayload.from_list(db_objects)
        assert len(storage_classes.remote) == 1
        assert len(storage_classes.ultra_ssd) == 1
        assert "remote-1" in storage_classes.remote
        assert "ultra-1" in storage_classes.ultra_ssd

        # Test to_list
        storage_class_list = storage_classes.to_list()
        assert len(storage_class_list) == 2

        remote_classes = [sc for sc in storage_class_list if sc.type == StorageClassType.AZ_CABS]
        ultra_classes = [sc for sc in storage_class_list if sc.type == StorageClassType.AZ_USSD]

        assert len(remote_classes) == 1
        assert len(ultra_classes) == 1
        assert remote_classes[0].name == "remote-1"
        assert ultra_classes[0].name == "ultra-1"

    def test_roundtrip_conversion_maintains_data_integrity(self):
        """Test that converting to_list and from_list maintains data integrity."""
        original = StorageClassPayload(
            remote={
                "remote-1": AzureCrossAccountBlobStorage(
                    subscription_id="12345678-1234-1234-1234-123456789012",
                    storage_account="storage123",
                    resource_group="rg-prod",
                    sku_name=AzureStorageClassSKU.PREMIUM_LRS,
                    container="my-container",
                ),
            },
            ultra_ssd={
                "ultra-1": AzureUltraSSDStorageClass(iops=5000, throughput=500),
            },
        )

        # Convert to list and back
        storage_class_list = original.to_list()
        db_objects = [
            StorageClass(id=i + 1, cluster_id=1, type=sc.type, name=sc.name, config=sc.config)
            for i, sc in enumerate(storage_class_list)
        ]
        restored = StorageClassPayload.from_list(db_objects)

        assert len(restored.remote) == len(original.remote)
        assert len(restored.ultra_ssd) == len(original.ultra_ssd)
        assert restored.remote["remote-1"].subscription_id == "12345678-1234-1234-1234-123456789012"
        assert restored.remote["remote-1"].container == "my-container"
        assert restored.ultra_ssd["ultra-1"].iops == 5000

    @pytest.mark.parametrize(
        "operation, input_data, expected_remote, expected_ultra_ssd",
        [
            ("from_list", [], 0, 0),
            ("to_list", StorageClassPayload(remote={}, ultra_ssd={}), 0, None),
        ],
    )
    def test_empty_conversions(self, operation, input_data, expected_remote, expected_ultra_ssd):
        """Test from_list and to_list with empty data."""
        if operation == "from_list":
            storage_classes = StorageClassPayload.from_list(input_data)
            assert len(storage_classes.remote) == expected_remote
            assert len(storage_classes.ultra_ssd) == expected_ultra_ssd
        else:  # to_list
            storage_class_list = input_data.to_list()
            assert len(storage_class_list) == expected_remote

    @pytest.mark.parametrize(
        "storage_type, name, should_be_valid",
        [
            # Valid names
            ("remote", "azure-disk", True),
            ("remote", "standard", True),
            ("remote", "my-storage-class", True),
            ("remote", "s", True),
            ("remote", "a" * 63, True),  # Max length
            ("remote", "storage123", True),
            ("remote", "123storage", True),
            ("ultra_ssd", "ultra-ssd", True),
            ("ultra_ssd", "u", True),
            ("ultra_ssd", "ultra123", True),
            # Invalid names - special characters
            ("remote", "azure_disk", False),
            ("remote", "azure.disk", False),
            ("remote", "azure disk", False),
            ("ultra_ssd", "ultra_ssd", False),
            ("ultra_ssd", "ultra.ssd", False),
            # Invalid names - start/end with hyphen
            ("remote", "-azure-disk", False),
            ("remote", "azure-disk-", False),
            ("ultra_ssd", "-ultra", False),
            # Invalid names - empty
            ("remote", "", False),
            ("ultra_ssd", "", False),
            # Invalid names - too long (64 chars)
            ("remote", "a" * 64, False),
            ("ultra_ssd", "a" * 64, False),
        ],
    )
    def test_storage_class_name_validation_via_to_list(self, storage_type, name, should_be_valid):
        """Test that storage class names in dict keys are validated when converting to_list."""
        config_remote = AzureCrossAccountBlobStorage(
            subscription_id="12345678-1234-1234-1234-123456789012",
            storage_account="storage123",
            resource_group="rg-prod",
        )
        config_ultra = AzureUltraSSDStorageClass(iops=5000, throughput=500)

        if storage_type == "remote":
            storage_classes = StorageClassPayload(remote={name: config_remote})
        else:
            storage_classes = StorageClassPayload(ultra_ssd={name: config_ultra})

        if should_be_valid:
            # Should successfully convert to list
            storage_class_list = storage_classes.to_list()
            assert len(storage_class_list) == 1
            assert storage_class_list[0].name == name
        else:
            # Should fail when trying to create StorageClassBase with invalid name
            with pytest.raises(ValidationError):
                storage_classes.to_list()


@pytest.mark.unit
@pytest.mark.models
@pytest.mark.remote_storage_classes
class TestAzureCrossAccountBlobStorage:
    """Unit tests for AzureCrossAccountBlobStorage model validation."""

    def test_azure_cross_account_blob_storage_with_all_fields(self):
        """Test creating AzureCrossAccountBlobStorage with all fields."""
        storage = AzureCrossAccountBlobStorage(
            subscription_id="12345678-1234-1234-1234-123456789012",
            storage_account="mystorageaccount",
            resource_group="my-resource-group",
            sku_name=AzureStorageClassSKU.PREMIUM_LRS,
            container="my-container",
        )

        assert storage.subscription_id == "12345678-1234-1234-1234-123456789012"
        assert storage.storage_account == "mystorageaccount"
        assert storage.resource_group == "my-resource-group"
        assert storage.sku_name == AzureStorageClassSKU.PREMIUM_LRS
        assert storage.container == "my-container"

    def test_azure_cross_account_blob_storage_without_optional_fields(self):
        """Test creating AzureCrossAccountBlobStorage without optional fields."""
        storage = AzureCrossAccountBlobStorage(
            subscription_id="12345678-1234-1234-1234-123456789012",
            storage_account="mystorageaccount",
            resource_group="my-resource-group",
        )

        assert storage.subscription_id == "12345678-1234-1234-1234-123456789012"
        assert storage.storage_account == "mystorageaccount"
        assert storage.resource_group == "my-resource-group"
        assert storage.sku_name == AzureStorageClassSKU.STANDARD_LRS  # Default value
        assert storage.container is None

    def test_azure_cross_account_blob_storage_required_fields(self):
        """Test that required fields cannot be omitted."""
        with pytest.raises(ValidationError) as exc_info:
            AzureCrossAccountBlobStorage(
                storage_account="mystorageaccount",
                resource_group="my-resource-group",
            )

        errors = exc_info.value.errors()
        assert any(error["loc"][0] == "subscription_id" for error in errors)

    @pytest.mark.parametrize(
        "sku_name",
        [
            AzureStorageClassSKU.STANDARD_LRS,
            AzureStorageClassSKU.PREMIUM_LRS,
        ],
    )
    def test_azure_cross_account_blob_storage_valid_sku_names(self, sku_name):
        """Test that all valid SKU names are accepted."""
        storage = AzureCrossAccountBlobStorage(
            subscription_id="12345678-1234-1234-1234-123456789012",
            storage_account="mystorageaccount",
            resource_group="my-resource-group",
            sku_name=sku_name,
        )

        assert storage.sku_name == sku_name

    @pytest.mark.parametrize(
        "container, should_be_valid",
        [
            # Valid container names (same regex as storage class names)
            ("my-container", True),
            ("container123", True),
            ("123container", True),
            ("c", True),  # Single character
            ("a" * 63, True),  # Max length
            ("my-very-long-container-name-123", True),
            (None, True),  # Optional field
            # Invalid container names - special characters
            ("my_container", False),
            ("my.container", False),
            ("my container", False),
            ("my/container", False),
            # Invalid container names - start/end with hyphen
            ("-container", False),
            ("container-", False),
            # Invalid container names - empty string
            ("", False),
            # Invalid container names - too long (64 chars)
            ("a" * 64, False),
        ],
    )
    def test_container_name_validation(self, container, should_be_valid):
        """Test that container names follow the same validation rules as storage class names."""
        if should_be_valid:
            storage = AzureCrossAccountBlobStorage(
                subscription_id="12345678-1234-1234-1234-123456789012",
                storage_account="mystorageaccount",
                resource_group="my-resource-group",
                container=container,
            )
            assert storage.container == container
        else:
            with pytest.raises(ValidationError) as exc_info:
                AzureCrossAccountBlobStorage(
                    subscription_id="12345678-1234-1234-1234-123456789012",
                    storage_account="mystorageaccount",
                    resource_group="my-resource-group",
                    container=container,
                )

            errors = exc_info.value.errors()
            assert any(error["loc"][0] == "container" for error in errors)


@pytest.mark.unit
@pytest.mark.models
@pytest.mark.ultra_ssd_storage_classes
class TestAzureUltraSSDStorageClass:
    """Unit tests for AzureUltraSSDStorageClass model validation."""

    def test_azure_ultra_ssd_with_valid_values(self):
        """Test creating AzureUltraSSDStorageClass with valid values."""
        storage = AzureUltraSSDStorageClass(iops=5000, throughput=500)

        assert storage.iops == 5000
        assert storage.throughput == 500

    @pytest.mark.parametrize(
        "iops, should_be_valid",
        [
            # Valid IOPS values
            (1200, True),  # Minimum boundary
            (5000, True),  # Mid-range
            (10000, True),  # Mid-range
            (100000, True),  # High
            (400000, True),  # Maximum boundary
            # Invalid IOPS values - below minimum
            (1199, False),
            (1000, False),
            (500, False),
            (0, False),
            (-100, False),
            # Invalid IOPS values - above maximum
            (400001, False),
            (500000, False),
            (1000000, False),
        ],
    )
    def test_azure_ultra_ssd_iops_validation(self, iops, should_be_valid):
        """Test that IOPS values are within limits (1200-400000)."""
        if should_be_valid:
            storage = AzureUltraSSDStorageClass(iops=iops, throughput=500)
            assert storage.iops == iops
        else:
            with pytest.raises(ValidationError) as exc_info:
                AzureUltraSSDStorageClass(iops=iops, throughput=500)

            errors = exc_info.value.errors()
            assert any(error["loc"][0] == "iops" for error in errors)

    @pytest.mark.parametrize(
        "throughput, should_be_valid",
        [
            # Valid throughput values
            (300, True),  # Minimum boundary
            (500, True),  # Mid-range
            (1000, True),  # Mid-range
            (5000, True),  # High
            (10000, True),  # Maximum boundary
            # Invalid throughput values - below minimum
            (299, False),
            (200, False),
            (0, False),
            (-100, False),
            # Invalid throughput values - above maximum
            (10001, False),
            (15000, False),
        ],
    )
    def test_azure_ultra_ssd_throughput_validation(self, throughput, should_be_valid):
        """Test that throughput values are within limits (300-10000 MB/s)."""
        if should_be_valid:
            storage = AzureUltraSSDStorageClass(iops=5000, throughput=throughput)
            assert storage.throughput == throughput
        else:
            with pytest.raises(ValidationError) as exc_info:
                AzureUltraSSDStorageClass(iops=5000, throughput=throughput)

            errors = exc_info.value.errors()
            assert any(error["loc"][0] == "throughput" for error in errors)

    @pytest.mark.parametrize(
        "missing_field, kwargs",
        [
            ("throughput", {"iops": 5000}),
            ("iops", {"throughput": 500}),
        ],
    )
    def test_azure_ultra_ssd_required_fields(self, missing_field, kwargs):
        """Test that both IOPS and throughput fields are required."""
        with pytest.raises(ValidationError) as exc_info:
            AzureUltraSSDStorageClass(**kwargs)

        errors = exc_info.value.errors()
        assert any(error["loc"][0] == missing_field for error in errors)


@pytest.mark.unit
@pytest.mark.models
@pytest.mark.storage_classes
class TestStorageClassBase:
    """Unit tests for StorageClassBase model validation."""

    @pytest.mark.parametrize(
        "storage_type, name, config",
        [
            (
                StorageClassType.AZ_CABS,
                "my-storage-class",
                AzureCrossAccountBlobStorage(
                    subscription_id="12345678-1234-1234-1234-123456789012",
                    storage_account="mystorageaccount",
                    resource_group="my-resource-group",
                    sku_name=AzureStorageClassSKU.PREMIUM_LRS,
                ),
            ),
            (
                StorageClassType.AZ_USSD,
                "my-ultra-ssd",
                AzureUltraSSDStorageClass(iops=5000, throughput=500),
            ),
        ],
    )
    def test_storage_class_base_with_config(self, storage_type, name, config):
        """Test creating StorageClassBase with different config types."""
        storage_class = StorageClassBase(type=storage_type, name=name, config=config)

        assert storage_class.type == storage_type
        assert storage_class.name == name
        assert storage_class.config == config.model_dump()

    @pytest.mark.parametrize(
        "name, should_be_valid",
        [
            # Valid names
            ("azure-disk", True),
            ("standard", True),
            ("my-storage-class", True),
            ("s", True),  # Single character
            ("a" * 63, True),  # Max length
            ("storage123", True),
            ("123storage", True),
            ("my-long-storage-class-name-123", True),
            # Invalid names - special characters
            ("azure_disk", False),
            ("azure.disk", False),
            ("azure disk", False),
            ("azure/disk", False),
            # Invalid names - start/end with hyphen
            ("-azure-disk", False),
            ("azure-disk-", False),
            # Invalid names - empty
            ("", False),
            # Invalid names - too long
            ("a" * 64, False),
        ],
    )
    def test_storage_class_base_name_validation(self, name, should_be_valid):
        """Test that storage class names follow Kubernetes naming conventions."""
        config = AzureUltraSSDStorageClass(iops=5000, throughput=500)

        if should_be_valid:
            storage_class = StorageClassBase(type=StorageClassType.AZ_USSD, name=name, config=config)
            assert storage_class.name == name
        else:
            with pytest.raises(ValidationError):
                StorageClassBase(type=StorageClassType.AZ_USSD, name=name, config=config)

    @pytest.mark.parametrize(
        "missing_field, kwargs",
        [
            ("type", {"name": "my-storage", "config": AzureUltraSSDStorageClass(iops=5000, throughput=500)}),
            (
                "name",
                {"type": StorageClassType.AZ_USSD, "config": AzureUltraSSDStorageClass(iops=5000, throughput=500)},
            ),
            ("config", {"type": StorageClassType.AZ_USSD, "name": "my-storage"}),
        ],
    )
    def test_storage_class_base_required_fields(self, missing_field, kwargs):
        """Test that type, name, and config fields are required."""
        with pytest.raises(ValidationError) as exc_info:
            StorageClassBase(**kwargs)

        errors = exc_info.value.errors()
        assert any(error["loc"][0] == missing_field for error in errors)
