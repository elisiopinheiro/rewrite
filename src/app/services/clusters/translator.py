"""Cluster translator — syncs nested/association fields on create/patch."""

from typing import Any

from app.models.cluster import Cluster, ClusterFeature
from app.models.feature import Feature
from app.models.namespace import ClientNamespace
from app.models.node_pool import AdditionalNodePool
from app.models.otlp_endpoint import ClientOTLPEndpoint
from app.models.storage_class import StorageClass
from app.models.user_feature import UserFeature
from app.models.webhook import TeamsWebhook
from app.repositories.feature import FeatureRepository
from app.repositories.release import ReleaseRepository
from app.schemas.enums import Provider
from app.schemas.features import FeatureCreate
from app.schemas.otlp_endpoints import ClientOTLPEndpointWrite
from app.schemas.storage_classes import StorageClassPayloadWrite
from app.schemas.webhooks import TeamsWebhookWrite


class ClusterTranslator:
    """Handles syncing nested/association fields when creating or patching a cluster."""

    def sync_nested_fields(
        self,
        *,
        cluster: Cluster,
        payload: dict[str, Any],
        release_name: str | None = None,
        feature_repository: FeatureRepository,
        release_repository: ReleaseRepository,
    ) -> None:
        if "features" in payload:
            self._set_cluster_features(
                cluster=cluster,
                release_name=release_name or cluster.release,
                requested_features=payload.get("features") or [],
                feature_repository=feature_repository,
                release_repository=release_repository,
            )
        if "client_namespaces" in payload:
            cluster.client_namespaces = [ClientNamespace(**item) for item in (payload.get("client_namespaces") or [])]
        if "additional_node_pools" in payload:
            cluster.additional_node_pools = [
                AdditionalNodePool(**item) for item in (payload.get("additional_node_pools") or [])
            ]
        if "user_features" in payload:
            cluster.user_features = [
                UserFeature(**{**item, "cluster_id": cluster.id}) for item in (payload.get("user_features") or [])
            ]
        if "teams_webhooks" in payload:
            webhooks = payload.get("teams_webhooks")
            if webhooks is None:
                cluster.teams_webhooks = []
            else:
                webhooks_payload = (
                    TeamsWebhookWrite.model_validate(webhooks) if isinstance(webhooks, dict) else webhooks
                )
                cluster.teams_webhooks = [
                    TeamsWebhook(
                        type=item.webhook_type,
                        level=item.level,
                        url=item.url,
                        webhook_id=item.webhook_id,
                    )
                    for item in webhooks_payload.to_items(cluster.name)
                ]
        if "client_otlp_endpoints" in payload:
            cluster.client_otlp_endpoints = [
                ClientOTLPEndpoint(**self._to_persistence_otlp_endpoint(item))
                for item in (payload.get("client_otlp_endpoints") or [])
            ]
        if cluster.provider == Provider.AZURE.value and "storage_classes" in payload:
            storage_classes = payload.get("storage_classes")
            storage_classes_payload = (
                StorageClassPayloadWrite.model_validate(storage_classes)
                if isinstance(storage_classes, dict)
                else storage_classes
            )
            cluster.storage_classes = [
                StorageClass(**item)
                for item in (
                    storage_classes_payload.to_entries()
                    if isinstance(storage_classes_payload, StorageClassPayloadWrite)
                    else []
                )
            ]

    def _set_cluster_features(
        self,
        *,
        cluster: Cluster,
        release_name: str,
        requested_features: list[dict[str, Any]],
        feature_repository: FeatureRepository,
        release_repository: ReleaseRepository,
    ) -> None:
        if not requested_features:
            # Match legacy semantics: an empty list is a no-op, not a wipe of all
            # (including core) features. Features are only ever rebuilt from a
            # non-empty request. This protects the shared DB the legacy app reads.
            return

        release_matches = release_repository.list_by_name_and_provider(
            name=release_name.lower(), provider=cluster.provider
        )
        if not release_matches:
            raise ValueError(f"Release {release_name} not found")

        db_features = feature_repository.list_features()
        features_by_name = {feature["name"]: feature for feature in requested_features if feature.get("enabled")}
        release = release_matches[0]
        cluster_features: list[ClusterFeature] = []

        for release_feature in release.features:
            feature = release_feature.feature
            selected_feature = features_by_name.get(feature.name)
            # Find matching persisted feature or use the release's feature definition
            persisted_feature = next(
                (
                    db_feature
                    for db_feature in db_features
                    if FeatureCreate(
                        name=db_feature.name,
                        feature_type=db_feature.type,
                        dependencies=db_feature.dependencies,
                        constraints=db_feature.constraints,
                        namespaced=db_feature.namespaced,
                    )
                    == FeatureCreate(
                        name=feature.name,
                        feature_type=feature.type,
                        dependencies=feature.dependencies,
                        constraints=feature.constraints,
                        namespaced=feature.namespaced,
                    )
                ),
                Feature(
                    name=feature.name,
                    type=feature.type,
                    dependencies=feature.dependencies,
                    constraints=feature.constraints,
                    namespaced=feature.namespaced,
                ),
            )
            cluster_features.append(
                ClusterFeature(
                    feature=persisted_feature,
                    cluster=cluster,
                    enabled=bool(selected_feature),
                    config=selected_feature.get("config") if selected_feature else None,
                )
            )

        cluster.features = cluster_features

    @staticmethod
    def _to_persistence_otlp_endpoint(item: dict[str, Any]) -> dict[str, Any]:
        """Map public schema field names to persistence field names."""
        endpoint = ClientOTLPEndpointWrite.model_validate(item) if isinstance(item, dict) else item
        payload = endpoint.model_dump(mode="json", exclude_none=True)
        auth = payload.get("auth")
        if auth is not None:
            payload["auth"] = {**auth, "type": auth.pop("auth_type")}
        payload["type"] = payload.pop("endpoint_type")
        return payload
