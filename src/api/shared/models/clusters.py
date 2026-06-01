from datetime import datetime, timezone
from typing import Annotated, Dict, List, Literal, Optional, Union
from zoneinfo import ZoneInfo

from pydantic import (
    BaseModel,
    ConfigDict,
    SerializeAsAny,
    StringConstraints,
    TypeAdapter,
)
from pydantic import Field as PydanticField
from sqlalchemy import String as SAString
from sqlmodel import (
    JSON,
    Column,
    Field,
    Relationship,
    SQLModel,
    UniqueConstraint,
    text,
)

from api.shared.config import DB_TABLE_RELATIONSHIP_DEFAULTS as RELATIONSHIP_DEFAULTS
from api.shared.config import SCALING_PERIOD_PATTERN, WEEKDAYS
from api.shared.enums import AzureSkuTier, ClusterStatus, Environment, Provider
from api.shared.exceptions import InvalidProviderException
from api.shared.models.client_namespaces import ClientNamespace, ClientNamespaceBase
from api.shared.models.client_otlp_endpoints import (
    ClientOTLPEndpoint,
    ClientOTLPEndpointBase,
)
from api.shared.models.features import Feature, FeatureBaseEnable
from api.shared.models.nodes import AdditionalNodePool, AdditionalNodePoolBase
from api.shared.models.operation import Operation
from api.shared.models.storage_classes import StorageClass, StorageClassPayload
from api.shared.models.teams_webhooks import TeamsWebhook, TeamsWebhookBase, TeamsWebhookRequest
from api.shared.models.user_features import UserFeature, UserFeatureBase


class ClusterLock(SQLModel, table=True):
    cluster_name: str = Field(foreign_key="cluster.name", nullable=False, primary_key=True)
    locked: bool
    owner: Optional[str] = None
    token: Optional[str] = None
    timeout_at: datetime  # UTC
    created_at: datetime  # UTC
    updated_at: datetime  # UTC

    cluster: Optional["Cluster"] = Relationship(
        back_populates="cluster_lock",
        sa_relationship_kwargs={
            "lazy": "noload",
        },
    )


class LockResponse(BaseModel):
    """Response model for successful cluster lock"""

    message: str
    token: str


class UnlockResponse(BaseModel):
    """Response model for successful cluster unlock"""

    message: str


class ClusterFeature(SQLModel, table=True):
    cluster_id: Optional[int] = Field(default=None, foreign_key="cluster.id", primary_key=True)
    feature_id: Optional[int] = Field(default=None, foreign_key="feature.id", primary_key=True)
    enabled: Optional[bool] = False
    config: Optional[Dict] = Field(sa_column=Column(JSON, nullable=True, default=None))

    cluster: "Cluster" = Relationship(
        back_populates="features",
        sa_relationship_kwargs={
            "lazy": "joined",
        },
    )
    feature: "Feature" = Relationship(
        back_populates="clusters",
        sa_relationship_kwargs={
            "lazy": "joined",
        },
    )


class Cluster(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("name", name="cluster_name_uc"),)

    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    operations: List[Operation] = Relationship(sa_relationship_kwargs={"cascade": "all"})
    name: str  # Should be unique
    subscription: str
    account_name: Optional[str] = Field(sa_column_kwargs={"server_default": "", "nullable": False})
    provider: Provider = Field(sa_type=SAString)
    release: str
    environment: Environment = Field(sa_type=SAString)
    internal: bool
    repository: str = Field(sa_column_kwargs={"unique": True})
    # https://stackoverflow.com/questions/12045698/sqlalchemy-boolean-value-is-none#comment69750602_12045897
    multi_tenant: bool = Field(default=False, sa_column_kwargs={"server_default": "f", "nullable": False})
    node_min_count: int
    node_max_count: int
    provider_region: str
    tshirt_size: str
    infra_revision: str
    kubernetes_version: str
    appd_id: Optional[str] = None
    authorized_api_ip_ranges: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    dns_zone: Optional[str] = None
    logging_retention_period: Optional[str] = None
    tracing_retention_period: Optional[str] = None
    pod_cidr: Optional[str] = None
    service_cidr: Optional[str] = None
    owner_group: Optional[str] = None
    cmdb_app_id: Optional[str] = None
    cmdb_appd_id: Optional[str] = None
    network_cidr: str = Field(sa_column_kwargs={"server_default": "0.0.0.0/0"})
    status: Optional[ClusterStatus] = Field(
        default=None,
        sa_column=Column(SAString, server_default=ClusterStatus.RUNNING.value),
    )
    kubedownscaler_downscale_period: Optional[str] = None  # Remove after 3.41.0
    kubedownscaler_upscale_period: Optional[str] = None  # Remove after 3.41.0
    uptime_period: Optional[Annotated[str, StringConstraints(pattern=SCALING_PERIOD_PATTERN)]] = None
    gateway_api_enabled: Optional[bool] = Field(default=False, sa_column_kwargs={"server_default": "f"}, nullable=False)
    headlamp_enabled: Optional[bool] = Field(
        default=False,
        sa_column_kwargs={"server_default": "f"},
        nullable=False,
    )
    domain_allowlist: Optional[List[str]] = Field(sa_column=Column(JSON), default=[])
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
        nullable=False,
    )
    updated_at: Optional[datetime] = Field(default=None, nullable=True)
    cluster_lock: Optional[ClusterLock] = Relationship(
        back_populates="cluster",
        sa_relationship_kwargs={
            "lazy": "joined",
            "cascade": "all, delete-orphan",
            "uselist": False,
        },
    )
    client_namespaces: List[ClientNamespace] = Relationship(
        back_populates="cluster", sa_relationship_kwargs=RELATIONSHIP_DEFAULTS
    )
    features: Optional[List[ClusterFeature]] = Relationship(
        back_populates="cluster", sa_relationship_kwargs=RELATIONSHIP_DEFAULTS
    )
    user_features: Optional[List[UserFeature]] = Relationship(
        back_populates="cluster", sa_relationship_kwargs=RELATIONSHIP_DEFAULTS
    )
    additional_node_pools: List[AdditionalNodePool] = Relationship(
        back_populates="cluster", sa_relationship_kwargs=RELATIONSHIP_DEFAULTS
    )
    teams_webhooks: List[TeamsWebhook] = Relationship(
        back_populates="cluster", sa_relationship_kwargs=RELATIONSHIP_DEFAULTS
    )
    client_otlp_endpoints: List[ClientOTLPEndpoint] = Relationship(
        back_populates="cluster", sa_relationship_kwargs=RELATIONSHIP_DEFAULTS
    )

    # AWS specific fields
    aws_vpc: Optional[str] = None
    aws_vpc_endpoint_remote_account_ids: Optional[List[str]] = Field(sa_column=Column(JSON), default=[""])
    aws_remote_account_ids: Optional[List[str]] = Field(sa_column=Column(JSON), default=[""])
    vpc_endpoint_service_name: Optional[str] = ""
    vpc_endpoint_service_ingress_name: Optional[str] = ""
    cluster_oidc_issuer_url: Optional[str] = ""

    # Azure specific fields
    azure_sku_tier: Optional[AzureSkuTier] = Field(default=None, sa_type=SAString)
    azure_subnet_name: Optional[str] = ""
    azure_vnet_name: Optional[str] = ""
    azure_vnet_resource_group: Optional[str] = ""
    dns_service_ip: Optional[str] = ""
    mi_agentpool_object_id: Optional[str] = ""
    mi_cluster_object_id: Optional[str] = ""
    storage_classes: List["StorageClass"] = Relationship(
        back_populates="cluster", sa_relationship_kwargs=RELATIONSHIP_DEFAULTS
    )

    def _process_uptime_period(self):
        match = SCALING_PERIOD_PATTERN.match(self.uptime_period)
        weekday_start = match.group("startweekday").upper()
        weekday_end = match.group("endweekday").upper()
        start_time = match.group("starthour")
        end_time = match.group("endhour")
        tz = match.group("timezone")
        return weekday_start, weekday_end, start_time, end_time, tz

    def _is_in_downtime_window(self) -> bool:
        if not self.uptime_period:
            return False

        up_start_day, up_end_day, up_start_time, up_end_time, up_tz = self._process_uptime_period()
        now = datetime.now(tz=ZoneInfo(up_tz))
        weekday = now.strftime("%a").upper()
        today_idx = WEEKDAYS.index(weekday)
        up_start_day_idx = WEEKDAYS.index(up_start_day)
        up_end_day_idx = WEEKDAYS.index(up_end_day)

        if up_start_day_idx <= up_end_day_idx:
            in_weekday_range = up_start_day_idx <= today_idx <= up_end_day_idx
        else:
            # wraps around (e.g. Fri-Mon)
            in_weekday_range = today_idx >= up_start_day_idx or today_idx <= up_end_day_idx

        start = datetime.strptime(up_start_time, "%H:%M").time()
        end = datetime.strptime(up_end_time, "%H:%M").time()
        in_time_range = start <= now.time() < end
        in_uptime = in_weekday_range and in_time_range
        return not in_uptime

    def build_response(self) -> Union["ClusterAwsResponse", "ClusterAzureResponse"]:
        """
        Parses a cluster into a ClusterAwsResponse or ClusterAzureResponse.

        Args:
            cluster: The cluster to parse

        Returns:
            ClusterAwsResponse or ClusterAzureResponse
        """
        # Exclude fields that are added/transformed manually below
        # Note: Relationships are not included in the dict by default, thats why we need to manually add them
        cluster_dict = self.model_dump(
            exclude={
                "features",
                "user_features",
                "client_namespaces",
                "additional_node_pools",
                "teams_webhooks",
                "client_otlp_endpoints",
                "storage_classes",
            }
        )

        # Locked status from cluster_lock relationship
        now = datetime.now(tz=timezone.utc).replace(tzinfo=None)
        cluster_dict["locked"] = bool(
            self.cluster_lock and self.cluster_lock.locked and now < self.cluster_lock.timeout_at
        )

        if self.provider == Provider.AWS:
            response = ClusterAwsResponse.model_validate(cluster_dict)
        else:
            response = ClusterAzureResponse.model_validate(cluster_dict)
            response.storage_classes = StorageClassPayload.from_list(self.storage_classes)

        response.features = [
            FeatureBaseEnable.model_validate({
                **cluster_feature.feature.model_dump(),
                "enabled": cluster_feature.enabled,
                "config": cluster_feature.config,
            })
            for cluster_feature in self.features
        ]

        response.user_features = self.user_features
        response.client_namespaces = self.client_namespaces
        response.additional_node_pools = self.additional_node_pools
        response.teams_webhooks = self.teams_webhooks
        response.client_otlp_endpoints = self.client_otlp_endpoints
        response.is_in_downtime_window = self._is_in_downtime_window()

        return response

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True, use_enum_values=True)


class ClusterBase(BaseModel):
    name: str
    subscription: str
    account_name: Optional[str] = None
    provider: Provider
    release: str
    environment: Environment
    internal: bool
    repository: str
    multi_tenant: bool = False
    node_min_count: int
    node_max_count: int
    provider_region: str
    tshirt_size: str
    infra_revision: str
    kubernetes_version: str
    appd_id: Optional[str] = None
    authorized_api_ip_ranges: Optional[List[str]] = None
    dns_zone: Optional[str] = None
    logging_retention_period: Optional[str] = None
    tracing_retention_period: Optional[str] = None
    pod_cidr: Optional[str] = None
    service_cidr: Optional[str] = None
    owner_group: Optional[str] = None
    cmdb_app_id: Optional[str] = None
    cmdb_appd_id: Optional[str] = None
    network_cidr: str
    status: Optional[ClusterStatus] = None
    kubedownscaler_downscale_period: Optional[str] = None
    kubedownscaler_upscale_period: Optional[str] = None
    uptime_period: Optional[Annotated[str, StringConstraints(pattern=SCALING_PERIOD_PATTERN)]] = None
    gateway_api_enabled: Optional[bool] = False
    headlamp_enabled: Optional[bool] = False
    domain_allowlist: Optional[List[str]] = []
    features: Optional[List[FeatureBaseEnable]] = None
    client_namespaces: Optional[List[ClientNamespaceBase]] = None
    additional_node_pools: Optional[List[AdditionalNodePoolBase]] = None
    client_otlp_endpoints: Optional[List[ClientOTLPEndpointBase]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ClusterAws(ClusterBase):
    provider: Literal[Provider.AWS]
    aws_vpc: str
    aws_vpc_endpoint_remote_account_ids: Optional[List[str]] = []
    aws_remote_account_ids: Optional[List[str]] = []
    vpc_endpoint_service_name: Optional[str] = ""
    vpc_endpoint_service_ingress_name: Optional[str] = ""
    cluster_oidc_issuer_url: Optional[str] = ""


class ClusterAzure(ClusterBase):
    provider: Literal[Provider.AZURE]
    azure_sku_tier: AzureSkuTier
    azure_subnet_name: str
    azure_vnet_name: str
    azure_vnet_resource_group: str
    dns_service_ip: str
    mi_agentpool_object_id: Optional[str] = None
    mi_cluster_object_id: Optional[str] = None
    storage_classes: Optional[StorageClassPayload] = None


class ClusterRequestBase(BaseModel):
    # teams_webhooks cant be in the ClusterBase model because request format is different from the response format
    teams_webhooks: Optional[TeamsWebhookRequest] = None


class ClusterAwsRequest(ClusterRequestBase, ClusterAws):
    pass


class ClusterAzureRequest(ClusterRequestBase, ClusterAzure):
    pass


class ClusterResponseBase(BaseModel):
    id: int
    # user_features cant be in the ClusterBase model because it is not an available field in the cluster request
    user_features: Optional[List[UserFeatureBase]] = []
    # teams_webhooks cant be in the ClusterBase model because response format is different from the request format
    teams_webhooks: Optional[List[SerializeAsAny[TeamsWebhookBase]]] = []
    # locked cant be in the ClusterBase model because it should only be in responses, not requests
    locked: bool
    # is_in_downtime_window cant be in the ClusterBase model because it is computed in response time
    is_in_downtime_window: bool = Field(default=False)


class ClusterAwsResponse(ClusterResponseBase, ClusterAws):
    pass


class ClusterAzureResponse(ClusterResponseBase, ClusterAzure):
    pass


class ClusterStatusResponse(BaseModel):
    """Response model for cluster status endpoints"""

    cluster_name: str
    status: str


class ClusterList(BaseModel):
    count: int
    clusters: Optional[
        List[
            SerializeAsAny[
                Annotated[
                    Union[ClusterAwsResponse, ClusterAzureResponse],
                    PydanticField(discriminator="provider"),
                ]
            ]
        ]
    ] = None


OrderByClusterFields = Literal["id", "name", "cmdb_app_id"]


class ClusterUpdateBase(BaseModel):
    release: Optional[str] = None
    node_min_count: Optional[int] = None
    node_max_count: Optional[int] = None
    tshirt_size: Optional[str] = None
    infra_revision: Optional[str] = None
    kubernetes_version: Optional[str] = None
    owner_group: Optional[str] = None
    cmdb_appd_id: Optional[str] = None
    environment: Optional[Environment] = None
    features: Optional[List[FeatureBaseEnable]] = None
    user_features: Optional[List[UserFeatureBase]] = None
    status: Optional[ClusterStatus] = None
    client_namespaces: Optional[List[ClientNamespaceBase]] = None
    logging_retention_period: Optional[str] = None
    tracing_retention_period: Optional[str] = None
    additional_node_pools: Optional[List[AdditionalNodePoolBase]] = None
    kubedownscaler_downscale_period: Optional[str] = None
    kubedownscaler_upscale_period: Optional[str] = None
    uptime_period: Optional[Annotated[str, StringConstraints(pattern=SCALING_PERIOD_PATTERN)]] = None
    multi_tenant: Optional[bool] = None
    gateway_api_enabled: Optional[bool] = None
    headlamp_enabled: Optional[bool] = None
    domain_allowlist: Optional[List[str]] = None
    teams_webhooks: Optional[TeamsWebhookRequest] = None
    client_otlp_endpoints: Optional[List[ClientOTLPEndpointBase]] = None


class ClusterAwsUpdate(ClusterUpdateBase):
    aws_vpc_endpoint_remote_account_ids: Optional[List[str]] = None
    aws_remote_account_ids: Optional[List[str]] = None
    vpc_endpoint_service_name: Optional[str] = None
    vpc_endpoint_service_ingress_name: Optional[str] = None
    cluster_oidc_issuer_url: Optional[str] = None


class ClusterAzureUpdate(ClusterUpdateBase):
    azure_sku_tier: Optional[AzureSkuTier] = None
    mi_agentpool_object_id: Optional[str] = None
    mi_cluster_object_id: Optional[str] = None
    storage_classes: Optional[StorageClassPayload] = None


class ClusterUpdateData(ClusterAwsUpdate, ClusterAzureUpdate):
    """This model inherits both provider specific models. It helps us to avoid using Union on the router."""

    def build_for_provider(self, provider: Provider, data) -> Union[ClusterAwsUpdate, ClusterAzureUpdate]:
        """This method was created to ensure that the correct model is used based on the provider"""
        if provider == Provider.AWS:
            return TypeAdapter(ClusterAwsUpdate).validate_python(data)
        elif provider == Provider.AZURE:
            return TypeAdapter(ClusterAzureUpdate).validate_python(data)
        else:
            raise InvalidProviderException(f"Invalid provider: {provider}")


class ClusterUpdateBackfill(ClusterUpdateBase):
    account_name: Optional[str] = None
    subscription: Optional[str] = None
    provider: Optional[str] = None
    internal: Optional[bool] = None
    repository: Optional[str] = None
    network_cidr: Optional[str] = None
    cmdb_app_id: Optional[str] = None
    appd_id: Optional[str] = None
    authorized_api_ip_ranges: Optional[List[str]] = None
    dns_zone: Optional[str] = None
    pod_cidr: Optional[str] = None
    service_cidr: Optional[str] = None
    dns_service_ip: Optional[str] = None
    aws_vpc: Optional[str] = None
    azure_subnet_name: Optional[str] = None
    azure_vnet_name: Optional[str] = None
    azure_vnet_resource_group: Optional[str] = None
    aws_vpc_endpoint_remote_account_ids: Optional[List[str]] = None
    aws_remote_account_ids: Optional[List[str]] = None
    vpc_endpoint_service_name: Optional[str] = None
    vpc_endpoint_service_ingress_name: Optional[str] = None
    cluster_oidc_issuer_url: Optional[str] = None
    azure_sku_tier: Optional[AzureSkuTier] = None
    mi_agentpool_object_id: Optional[str] = None
    mi_cluster_object_id: Optional[str] = None
    storage_classes: Optional[StorageClassPayload] = None
    created_at: Optional[datetime] = None
