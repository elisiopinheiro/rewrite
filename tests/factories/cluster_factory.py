from typing import Dict

import factory
from factory.alchemy import SQLAlchemyModelFactory
from factory.fuzzy import FuzzyChoice
from faker import Faker

from api.shared.enums import AzureSkuTier, Environment, Provider, WebhookLevel, WebhookType
from api.shared.models.clusters import (
    ClientNamespace,
    Cluster,
    TeamsWebhook,
)
from api.shared.models.nodes import AdditionalNodePool

fake = Faker()


# SQL Models Factories
class BaseClusterFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Cluster
        sqlalchemy_session_persistence = "commit"

    name = factory.Sequence(lambda n: f"test-cluster-{n}")
    subscription = factory.Faker("uuid4")
    release = "development"
    environment = FuzzyChoice(Environment)
    internal = factory.Faker("boolean")
    repository = factory.Faker("uuid4")
    node_min_count = factory.Faker("random_int", min=1, max=2)
    node_max_count = factory.Faker("random_int", min=3, max=10)
    provider_region = factory.Faker("random_element", elements=["eu-central-1", "eu-west-1", "us-east-1"])
    tshirt_size = factory.Faker("random_element", elements=["s", "m", "l", "xl"])
    kubernetes_version = factory.Faker("numerify", text="1.##")
    infra_revision = factory.Faker("numerify", text="1.#.#")
    uptime_period = None


class AWSClusterFactory(BaseClusterFactory):
    provider = Provider.AWS.value
    aws_vpc = "vpc-123456"


class AzureClusterFactory(BaseClusterFactory):
    provider = Provider.AZURE.value
    azure_sku_tier = FuzzyChoice(AzureSkuTier)
    azure_subnet_name = "test-subnet"
    azure_vnet_name = "test-vnet"
    azure_vnet_resource_group = "test-rg"
    dns_service_ip = "10.0.0.10"
    mi_agentpool_object_id = "1333c0e8-f2c8-4d06-a91f-9b6c89089915"
    mi_cluster_object_id = "75aa0665-b25e-460f-8858-fdb93672bbf5"


class TeamsWebhookFactory(SQLAlchemyModelFactory):
    class Meta:
        model = TeamsWebhook
        sqlalchemy_session_persistence = "commit"

    type = FuzzyChoice(WebhookType)
    level = FuzzyChoice(WebhookLevel)
    url = factory.Faker("url", schemes=["https"])
    webhook_id = factory.Faker("uuid4")


class ClientNamespaceFactory(SQLAlchemyModelFactory):
    class Meta:
        model = ClientNamespace
        sqlalchemy_session_persistence = "commit"

    name = factory.Sequence(lambda n: f"test-namespace-{n}")
    consumed_by = factory.Faker("bothify", text="APPD-######")
    admin = factory.List(["APPL_4WM_default_admin"])
    viewer = factory.List(["APPL_4WM_default_view"])
    editor = factory.List(["APPL_4WM_default_edit"])


class AdditionalNodePoolFactory(SQLAlchemyModelFactory):
    class Meta:
        model = AdditionalNodePool
        sqlalchemy_session_persistence = "commit"

    name = factory.LazyFunction(lambda: f"nodepool{fake.random_int(min=1, max=99)}")
    node_min_count = factory.Faker("random_int", min=0, max=3)
    node_max_count = factory.Faker("random_int", min=3, max=10)
    tshirt_size = "ram-s"


def make_add_cluster_payload(provider: Provider, **overrides) -> Dict:
    """Create cluster test data.

    Args:
        provider: The cloud provider for the cluster. Must be Provider.AWS or Provider.AZURE.
        overrides: Optional dictionary of values to override the default cluster data.

    Returns:
        Dict containing the cluster data.

    Raises:
        ValueError: If provider is not Provider.AWS or Provider.AZURE.
    """
    if provider not in [Provider.AWS, Provider.AZURE]:
        raise ValueError(f"Provider must be Provider.AWS or Provider.AZURE, got {provider}")

    base_data = {
        # Mandatory fields
        "name": f"test-cluster-{fake.uuid4()}",
        "subscription": f"test-sub-{fake.uuid4()}",
        "provider": provider.value,  # Use .value to get the string representation
        "release": "development",
        "environment": "development",
        "internal": True,
        "repository": f"test-repo-{fake.uuid4()}",
        "multi_tenant": False,
        "node_min_count": 1,
        "node_max_count": 3,
        "provider_region": "eu-central-1",
        "tshirt_size": "s",
        "infra_revision": "1.0.0",
        "kubernetes_version": "1.30",
        "network_cidr": "10.0.0.0/8",
        # Optional fields
        "account_name": f"{provider.value}-development",
        "appd_id": f"APPD-{fake.uuid4()}",
        "authorized_api_ip_ranges": [],
        "dns_zone": "development.4wm.cloud",
        "logging_retention_period": "168h",
        "tracing_retention_period": "168h",
        "pod_cidr": "10.0.0.0/16",
        "service_cidr": "10.1.0.0/16",
        "owner_group": "dev-group",
        "cmdb_app_id": "",
        "cmdb_appd_id": "",
        "status": "running",
        "kubedownscaler_downscale_period": "Mon-Fri 19:00-19:15 Europe/Lisbon",
        "kubedownscaler_upscale_period": "Mon-Fri 07:00-07:15 Europe/Lisbon",
        "uptime_period": None,
        "gateway_api_enabled": False,
        "headlamp_enabled": True,
        "domain_allowlist": [],
        "features": [],
        "user_features": [],
        "client_namespaces": [],
        "additional_node_pools": [],
        "teams_webhooks": {},
        "client_otlp_endpoints": [],
    }

    if provider == Provider.AWS:
        base_data.update({
            # Mandatory fields
            "aws_vpc": "vpc-123456",
            # Optional fields
            "aws_vpc_endpoint_remote_account_ids": [],
            "aws_remote_account_ids": [],
            "vpc_endpoint_service_name": "",
            "vpc_endpoint_service_ingress_name": "",
            "cluster_oidc_issuer_url": "",
        })
    elif provider == Provider.AZURE:
        base_data.update({
            # Mandatory fields
            "azure_sku_tier": "Free",
            "azure_subnet_name": "test-subnet",
            "azure_vnet_name": "test-vnet",
            "azure_vnet_resource_group": "test-rg",
            "dns_service_ip": "10.0.0.10",
            "mi_agentpool_object_id": f"{fake.uuid4()}",
            "mi_cluster_object_id": f"{fake.uuid4()}",
            # Optional fields
            "storage_classes": {
                "remote": {},
                "ultra_ssd": {},
            },
        })

    if overrides:
        base_data.update(overrides)

    return base_data


def make_cluster_update_payload(provider: Provider, **overrides) -> Dict:
    """Create cluster update test data.

    Args:
        provider: The cloud provider for the cluster. Must be Provider.AWS or Provider.AZURE.
        overrides: Optional dictionary of values to override the default cluster update data.

    Returns:
        Dict containing the cluster update data.

    Raises:
        ValueError: If provider is not Provider.AWS or Provider.AZURE.
    """
    if provider not in [Provider.AWS, Provider.AZURE]:
        raise ValueError(f"Provider must be Provider.AWS or Provider.AZURE, got {provider}")

    base_data = {
        "release": "development",
        "node_min_count": fake.random_int(min=1, max=2),
        "node_max_count": fake.random_int(min=3, max=10),
        "tshirt_size": fake.random_element(elements=["s", "m", "l", "xl"]),
        "infra_revision": fake.numerify(text="1.#.#"),
        "kubernetes_version": fake.numerify(text="1.##"),
        "owner_group": f"dev-group-{fake.word()}",
        "cmdb_appd_id": f"APPD-{fake.uuid4()}",
        "environment": fake.random_element(
            elements=[
                "test",
                "development",
                "integration",
                "pre-production",
                "production",
            ]
        ),
        "features": [],
        "user_features": [],
        "status": fake.random_element(elements=["running", "freeze"]),
        "client_namespaces": [],
        "logging_retention_period": "168h",
        "tracing_retention_period": "168h",
        "additional_node_pools": [],
        "kubedownscaler_downscale_period": "Mon-Fri 19:00-19:15 Europe/Lisbon",
        "kubedownscaler_upscale_period": "Mon-Fri 07:00-07:15 Europe/Lisbon",
        "uptime_period": None,
        "multi_tenant": fake.boolean(),
        "gateway_api_enabled": fake.boolean(),
        "headlamp_enabled": fake.boolean(),
        "domain_allowlist": [],
        "teams_webhooks": {},
        "client_otlp_endpoints": [],
    }

    if provider == Provider.AWS:
        base_data.update({
            "aws_vpc_endpoint_remote_account_ids": [],
            "aws_remote_account_ids": [],
            "vpc_endpoint_service_name": f"com.amazonaws.vpce.{fake.uuid4()}",
            "vpc_endpoint_service_ingress_name": "",
            "cluster_oidc_issuer_url": "",
        })
    elif provider == Provider.AZURE:
        base_data.update({
            "azure_sku_tier": fake.random_element(elements=["Free", "Standard"]),
            "mi_agentpool_object_id": f"{fake.uuid4()}",
            "mi_cluster_object_id": f"{fake.uuid4()}",
            "storage_classes": {},
        })

    if overrides:
        base_data.update(overrides)

    return base_data


def make_cluster_backfill_payload(**overrides) -> Dict:
    """Create cluster backfill test data.

    Args:
        overrides: Optional dictionary of values to override the default cluster backfill data.

    Returns:
        Dict containing the cluster backfill data.

    Raises:
        ValueError: If provider is not 'aws' or 'azure'.
    """

    base_data = {
        "release": "development",
        "node_min_count": fake.random_int(min=1, max=2),
        "node_max_count": fake.random_int(min=3, max=10),
        "tshirt_size": fake.random_element(elements=["s", "m", "l", "xl"]),
        "infra_revision": fake.numerify(text="1.#.#"),
        "kubernetes_version": fake.numerify(text="1.##"),
        "owner_group": f"dev-group-{fake.word()}",
        "cmdb_appd_id": f"APPD-{fake.uuid4()}",
        "environment": fake.random_element(
            elements=[
                "test",
                "development",
                "integration",
                "pre-production",
                "production",
            ]
        ),
        "features": [],
        "user_features": [],
        "status": fake.random_element(elements=["running", "freeze"]),
        "client_namespaces": [],
        "logging_retention_period": "168h",
        "tracing_retention_period": "168h",
        "additional_node_pools": [],
        "kubedownscaler_downscale_period": "Mon-Fri 19:00-19:15 Europe/Lisbon",
        "kubedownscaler_upscale_period": "Mon-Fri 07:00-07:15 Europe/Lisbon",
        "uptime_period": None,
        "multi_tenant": fake.boolean(),
        "gateway_api_enabled": fake.boolean(),
        "headlamp_enabled": fake.boolean(),
        "domain_allowlist": [],
        "teams_webhooks": {},
        "client_otlp_endpoints": [],
        "account_name": f"test-account-{fake.uuid4()}",
        "subscription": f"test-sub-{fake.uuid4()}",
        "provider": fake.random_element(elements=["aws", "azure"]),
        "internal": True,
        "repository": f"test-repo-{fake.uuid4()}",
        "network_cidr": "10.0.0.0/8",
        "cmdb_app_id": "",
        "appd_id": f"APPD-{fake.uuid4()}",
        "authorized_api_ip_ranges": [],
        "dns_zone": "development.4wm.cloud",
        "pod_cidr": "10.0.0.0/16",
        "service_cidr": "10.1.0.0/16",
        "dns_service_ip": "10.0.0.10",
        "aws_vpc": "vpc-123456",
        "azure_subnet_name": "test-subnet",
        "azure_vnet_name": "test-vnet",
        "azure_vnet_resource_group": "test-rg",
        "aws_vpc_endpoint_remote_account_ids": [],
        "aws_remote_account_ids": [],
        "vpc_endpoint_service_name": "",
        "vpc_endpoint_service_ingress_name": "",
        "cluster_oidc_issuer_url": "",
        "azure_sku_tier": "Free",
        "mi_agentpool_object_id": f"{fake.uuid4()}",
        "mi_cluster_object_id": f"{fake.uuid4()}",
        "storage_classes": {},
    }

    if overrides:
        base_data.update(overrides)

    return base_data
