"""Model factories for test data generation."""

from typing import Any


def make_cluster_data(*, name: str = "test-cluster", provider: str = "aws", **overrides: Any) -> dict[str, Any]:
    """Generate valid cluster creation payload."""
    base: dict[str, Any] = {
        "name": name,
        "subscription": "sub-001",
        "provider": provider,
        "release": "v1.0",
        "environment": "development",
        "internal": False,
        "repository": f"https://github.com/org/{name}",
        "multi_tenant": False,
        "node_min_count": 3,
        "node_max_count": 9,
        "provider_region": "eu-west-1",
        "tshirt_size": "M",
        "infra_revision": "rev-001",
        "kubernetes_version": "1.28",
        "network_cidr": "10.0.0.0/16",
    }
    if provider == "aws":
        base.update(
            {
                "aws_vpc": "vpc-12345",
                "aws_vpc_endpoint_remote_account_ids": [],
                "aws_remote_account_ids": [],
                "vpc_endpoint_service_name": "",
                "vpc_endpoint_service_ingress_name": "",
                "cluster_oidc_issuer_url": "",
            }
        )
    elif provider == "azure":
        base.update(
            {
                "azure_sku_tier": "Standard",
                "azure_subnet_name": "subnet-1",
                "azure_vnet_name": "vnet-1",
                "azure_vnet_resource_group": "rg-1",
                "dns_service_ip": "10.0.0.10",
            }
        )
    base.update(overrides)
    return base


def make_release_data(*, name: str = "v1.0", provider: str = "aws", **overrides: Any) -> dict[str, Any]:
    """Generate valid release creation payload."""
    base: dict[str, Any] = {
        "name": name,
        "provider": provider,
        "reserved_namespaces": ["kube-system"],
        "features": [],
    }
    base.update(overrides)
    return base


def make_feature_data(*, name: str = "monitoring", **overrides: Any) -> dict[str, Any]:
    """Generate valid feature creation payload."""
    base: dict[str, Any] = {
        "name": name,
        "feature_type": "optional",
    }
    base.update(overrides)
    return base


def make_lock_request(*, owner: str | None = None, timeout_minutes: int = 360) -> dict[str, Any]:
    """Generate valid lock acquisition payload."""
    data: dict[str, Any] = {"timeout_minutes": timeout_minutes}
    if owner is not None:
        data["owner"] = owner
    return data


def make_operation_data(*, operation_type: str = "deploy", status: str = "success", **overrides: Any) -> dict[str, Any]:
    """Generate valid operation creation payload."""
    base: dict[str, Any] = {
        "operation_type": operation_type,
        "status": status,
        "cicd_url": "https://ci.example.com/builds/123",
        "cluster_repository": None,
    }
    base.update(overrides)
    return base
