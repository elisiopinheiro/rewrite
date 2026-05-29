"""Cluster mapper — ORM model to response schema conversion."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any, cast
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.models.cluster import Cluster
from app.schemas.clusters import AwsClusterRead, AzureClusterRead, ClusterRead
from app.schemas.enums import Provider
from app.schemas.features import FeatureToggleRead
from app.schemas.otlp_endpoints import ClientOTLPEndpointRead
from app.schemas.storage_classes import StorageClassPayloadRead
from app.schemas.webhooks import TeamsWebhookRead

# Uptime period pattern: "MON-FRI 08:00-18:00 Europe/Amsterdam"
_SCALING_PERIOD_PATTERN = re.compile(
    r"^(?P<startweekday>[a-zA-Z]{3})-(?P<endweekday>[a-zA-Z]{3}) "
    r"(?P<starthour>(\d\d):(\d\d))-(?P<endhour>(\d\d):(\d\d)) "
    r"(?P<timezone>[a-zA-Z/_]+)$"
)
_WEEKDAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]


class ClusterMapper:
    """Maps ORM Cluster to read schemas with computed fields."""

    def to_read_model(self, cluster: Cluster) -> ClusterRead:
        cluster_dict = {
            "id": cluster.id,
            "name": cluster.name,
            "subscription": cluster.subscription,
            "account_name": cluster.account_name,
            "provider": cluster.provider,
            "release": cluster.release,
            "environment": cluster.environment,
            "internal": cluster.internal,
            "repository": cluster.repository,
            "multi_tenant": cluster.multi_tenant,
            "node_min_count": cluster.node_min_count,
            "node_max_count": cluster.node_max_count,
            "provider_region": cluster.provider_region,
            "tshirt_size": cluster.tshirt_size,
            "infra_revision": cluster.infra_revision,
            "kubernetes_version": cluster.kubernetes_version,
            "appd_id": cluster.appd_id,
            "authorized_api_ip_ranges": cluster.authorized_api_ip_ranges,
            "dns_zone": cluster.dns_zone,
            "logging_retention_period": cluster.logging_retention_period,
            "tracing_retention_period": cluster.tracing_retention_period,
            "pod_cidr": cluster.pod_cidr,
            "service_cidr": cluster.service_cidr,
            "owner_group": cluster.owner_group,
            "cmdb_app_id": cluster.cmdb_app_id,
            "cmdb_appd_id": cluster.cmdb_appd_id,
            "network_cidr": cluster.network_cidr,
            "status": cluster.status,
            "uptime_period": cluster.uptime_period,
            "gateway_api_enabled": cluster.gateway_api_enabled,
            "domain_allowlist": cluster.domain_allowlist or [],
            "created_at": cluster.created_at,
            "updated_at": cluster.updated_at,
            "features": [
                FeatureToggleRead(
                    id=cluster_feature.feature.id,
                    name=cluster_feature.feature.name,
                    feature_type=cluster_feature.feature.type,
                    dependencies=cluster_feature.feature.dependencies,
                    constraints=cluster_feature.feature.constraints,
                    namespaced=cluster_feature.feature.namespaced,
                    enabled=cluster_feature.enabled,
                    config=cluster_feature.config,
                )
                for cluster_feature in (cluster.features or [])
            ],
            "user_features": [
                {
                    "name": item.name,
                    "namespace": item.namespace,
                    "repo_url": item.repo_url,
                    "commit_hash": item.commit_hash,
                    "helm_path": item.helm_path,
                    "values_path": item.values_path,
                }
                for item in (cluster.user_features or [])
            ],
            "client_namespaces": [
                {
                    "name": item.name,
                    "consumed_by": item.consumed_by,
                    "admin": item.admin,
                    "viewer": item.viewer,
                    "editor": item.editor,
                }
                for item in (cluster.client_namespaces or [])
            ],
            "additional_node_pools": [
                {
                    "name": item.name,
                    "node_min_count": item.node_min_count,
                    "node_max_count": item.node_max_count,
                    "tshirt_size": item.tshirt_size,
                }
                for item in (cluster.additional_node_pools or [])
            ],
            "teams_webhooks": [
                TeamsWebhookRead(
                    webhook_type=item.type,
                    level=item.level,
                    url=item.url,
                    webhook_id=item.webhook_id,
                )
                for item in (cluster.teams_webhooks or [])
            ],
            "client_otlp_endpoints": [
                ClientOTLPEndpointRead.model_validate(
                    self._to_public_otlp_endpoint(
                        {
                            "name": item.name,
                            "type": item.type,
                            "endpoint": item.endpoint,
                            "signals": item.signals,
                            "auth": item.auth,
                            "config": item.config,
                        }
                    )
                )
                for item in (cluster.client_otlp_endpoints or [])
            ],
        }
        cluster_dict["locked"] = self._is_locked(cluster)
        cluster_dict["is_in_downtime_window"] = self._is_in_downtime_window(cluster.uptime_period)

        if cluster.provider == Provider.AWS.value:
            cluster_dict.update(
                {
                    "aws_vpc": cluster.aws_vpc,
                    "aws_vpc_endpoint_remote_account_ids": cluster.aws_vpc_endpoint_remote_account_ids or [],
                    "aws_remote_account_ids": cluster.aws_remote_account_ids or [],
                    "vpc_endpoint_service_name": cluster.vpc_endpoint_service_name,
                    "vpc_endpoint_service_ingress_name": cluster.vpc_endpoint_service_ingress_name,
                    "cluster_oidc_issuer_url": cluster.cluster_oidc_issuer_url,
                }
            )
            return AwsClusterRead.model_validate(cluster_dict)
        else:
            cluster_dict.update(
                {
                    "azure_sku_tier": cluster.azure_sku_tier,
                    "azure_subnet_name": cluster.azure_subnet_name,
                    "azure_vnet_name": cluster.azure_vnet_name,
                    "azure_vnet_resource_group": cluster.azure_vnet_resource_group,
                    "dns_service_ip": cluster.dns_service_ip,
                    "mi_agentpool_object_id": cluster.mi_agentpool_object_id,
                    "mi_cluster_object_id": cluster.mi_cluster_object_id,
                    "storage_classes": StorageClassPayloadRead.from_entries(cluster.storage_classes or []),
                }
            )
            return AzureClusterRead.model_validate(cluster_dict)

    @staticmethod
    def _to_public_otlp_endpoint(item: dict[str, object]) -> dict[str, object]:
        """Map persistence field names to public schema field names."""
        auth = item.get("auth")
        payload = {**item, "endpoint_type": item.get("type")}
        payload.pop("type", None)
        if auth is not None:
            auth_payload = cast(dict[str, Any], auth)
            public_auth_payload = {**auth_payload, "auth_type": auth_payload.get("type")}
            public_auth_payload.pop("type", None)
            payload["auth"] = public_auth_payload
        return payload

    def is_locked(self, cluster: Cluster) -> bool:
        return self._is_locked(cluster)

    @staticmethod
    def _is_locked(cluster: Cluster) -> bool:
        now = datetime.now(UTC).replace(tzinfo=None)
        return bool(cluster.cluster_lock and cluster.cluster_lock.locked and now < cluster.cluster_lock.timeout_at)

    @staticmethod
    def _is_in_downtime_window(uptime_period: str | None) -> bool:
        """Check if current time is outside the uptime window (i.e., in downtime)."""
        if not uptime_period:
            return False

        match = _SCALING_PERIOD_PATTERN.match(uptime_period)
        if match is None:
            return False

        up_start_day = match.group("startweekday").upper()
        up_end_day = match.group("endweekday").upper()
        up_start_time = match.group("starthour")
        up_end_time = match.group("endhour")
        up_tz = match.group("timezone")

        try:
            now = datetime.now(tz=ZoneInfo(up_tz))
            weekday = now.strftime("%a").upper()
            today_idx = _WEEKDAYS.index(weekday)
            up_start_day_idx = _WEEKDAYS.index(up_start_day)
            up_end_day_idx = _WEEKDAYS.index(up_end_day)
            start = datetime.strptime(up_start_time, "%H:%M").time()
            end = datetime.strptime(up_end_time, "%H:%M").time()
        except (ValueError, IndexError, ZoneInfoNotFoundError):
            return False

        if up_start_day_idx <= up_end_day_idx:
            in_weekday_range = up_start_day_idx <= today_idx <= up_end_day_idx
        else:
            in_weekday_range = today_idx >= up_start_day_idx or today_idx <= up_end_day_idx

        in_time_range = start <= now.time() < end
        return not (in_weekday_range and in_time_range)
