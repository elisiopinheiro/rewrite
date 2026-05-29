"""Cluster table model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.feature import Feature
    from app.models.lock import ClusterLock
    from app.models.namespace import ClientNamespace
    from app.models.node_pool import AdditionalNodePool
    from app.models.operation import Operation
    from app.models.otlp_endpoint import ClientOTLPEndpoint
    from app.models.storage_class import StorageClass
    from app.models.user_feature import UserFeature
    from app.models.webhook import TeamsWebhook


class Cluster(Base):
    __tablename__ = "cluster"
    __table_args__ = (
        UniqueConstraint("name", name="cluster_name_uc"),
        UniqueConstraint("repository", name="cluster_repository_uc"),
    )

    # Identity
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)

    # Core fields (NOT NULL)
    subscription: Mapped[str] = mapped_column(nullable=False)
    provider: Mapped[str] = mapped_column(nullable=False)
    release: Mapped[str] = mapped_column(nullable=False)
    environment: Mapped[str] = mapped_column(nullable=False)
    internal: Mapped[bool] = mapped_column(nullable=False)
    repository: Mapped[str] = mapped_column(nullable=False)
    multi_tenant: Mapped[bool] = mapped_column(default=False, nullable=False)
    node_min_count: Mapped[int] = mapped_column(nullable=False)
    node_max_count: Mapped[int] = mapped_column(nullable=False)
    provider_region: Mapped[str] = mapped_column(nullable=False)
    tshirt_size: Mapped[str] = mapped_column(nullable=False)
    infra_revision: Mapped[str] = mapped_column(nullable=False)
    kubernetes_version: Mapped[str] = mapped_column(nullable=False)
    network_cidr: Mapped[str] = mapped_column(default="0.0.0.0/0", nullable=False)
    status: Mapped[str] = mapped_column(default="running", server_default="running", nullable=False)
    gateway_api_enabled: Mapped[bool] = mapped_column(default=False, server_default=text("false"), nullable=False)

    # Optional metadata (nullable)
    account_name: Mapped[str | None] = mapped_column(nullable=True)
    appd_id: Mapped[str | None] = mapped_column(nullable=True)
    dns_zone: Mapped[str | None] = mapped_column(nullable=True)
    owner_group: Mapped[str | None] = mapped_column(nullable=True)
    cmdb_app_id: Mapped[str | None] = mapped_column(nullable=True)
    cmdb_appd_id: Mapped[str | None] = mapped_column(nullable=True)
    pod_cidr: Mapped[str | None] = mapped_column(nullable=True)
    service_cidr: Mapped[str | None] = mapped_column(nullable=True)
    logging_retention_period: Mapped[str | None] = mapped_column(nullable=True)
    tracing_retention_period: Mapped[str | None] = mapped_column(nullable=True)
    uptime_period: Mapped[str | None] = mapped_column(nullable=True)
    domain_allowlist: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    authorized_api_ip_ranges: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    # AWS-specific (NULL for Azure clusters)
    aws_vpc: Mapped[str | None] = mapped_column(nullable=True)
    aws_vpc_endpoint_remote_account_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    aws_remote_account_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    vpc_endpoint_service_name: Mapped[str | None] = mapped_column(nullable=True)
    vpc_endpoint_service_ingress_name: Mapped[str | None] = mapped_column(nullable=True)
    cluster_oidc_issuer_url: Mapped[str | None] = mapped_column(nullable=True)

    # Azure-specific (NULL for AWS clusters)
    azure_sku_tier: Mapped[str | None] = mapped_column(nullable=True)
    azure_subnet_name: Mapped[str | None] = mapped_column(nullable=True)
    azure_vnet_name: Mapped[str | None] = mapped_column(nullable=True)
    azure_vnet_resource_group: Mapped[str | None] = mapped_column(nullable=True)
    dns_service_ip: Mapped[str | None] = mapped_column(nullable=True)
    mi_agentpool_object_id: Mapped[str | None] = mapped_column(nullable=True)
    mi_cluster_object_id: Mapped[str | None] = mapped_column(nullable=True)

    # Timestamps
    created_at: Mapped[datetime | None] = mapped_column(server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Relationships
    cluster_lock: Mapped[ClusterLock | None] = relationship(
        back_populates="cluster", cascade="all, delete-orphan", uselist=False
    )
    features: Mapped[list[ClusterFeature]] = relationship(back_populates="cluster", cascade="all, delete-orphan")
    client_namespaces: Mapped[list[ClientNamespace]] = relationship(
        back_populates="cluster", cascade="all, delete-orphan"
    )
    additional_node_pools: Mapped[list[AdditionalNodePool]] = relationship(
        back_populates="cluster", cascade="all, delete-orphan"
    )
    user_features: Mapped[list[UserFeature]] = relationship(back_populates="cluster", cascade="all, delete-orphan")
    teams_webhooks: Mapped[list[TeamsWebhook]] = relationship(back_populates="cluster", cascade="all, delete-orphan")
    client_otlp_endpoints: Mapped[list[ClientOTLPEndpoint]] = relationship(
        back_populates="cluster", cascade="all, delete-orphan"
    )
    storage_classes: Mapped[list[StorageClass]] = relationship(back_populates="cluster", cascade="all, delete-orphan")
    operations: Mapped[list[Operation]] = relationship(back_populates="cluster")


class ClusterFeature(Base):
    """Association table between clusters and features with extra attributes."""

    __tablename__ = "clusterfeature"

    cluster_id: Mapped[int] = mapped_column(ForeignKey("cluster.id", ondelete="CASCADE"), primary_key=True)
    feature_id: Mapped[int] = mapped_column(ForeignKey("feature.id", ondelete="CASCADE"), primary_key=True)
    enabled: Mapped[bool] = mapped_column(default=False, nullable=False)
    config: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    cluster: Mapped[Cluster] = relationship(back_populates="features")
    feature: Mapped[Feature] = relationship(back_populates="cluster_features")
