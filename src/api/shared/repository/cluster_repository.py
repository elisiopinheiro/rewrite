"""Cluster repository methods"""

from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional, Union
from uuid import uuid4

import sqlalchemy
from fastapi import Depends
from sqlalchemy import Integer, and_, asc, distinct, or_, select
from sqlalchemy.dialects.postgresql import ARRAY
from sqlmodel import Session

from api.shared.database import get_db
from api.shared.enums import ClusterStatus, Provider
from api.shared.exceptions import (
    ClusterLockNotFoundException,
    ClusterNotLockedException,
    LockException,
    LockTokenMismatchException,
    ReleaseNotFoundException,
)
from api.shared.logger import logger
from api.shared.models.client_namespaces import ClientNamespace
from api.shared.models.client_otlp_endpoints import (
    ClientOTLPEndpoint,
    ClientOTLPEndpointBase,
)
from api.shared.models.clusters import (
    Cluster,
    ClusterAwsRequest,
    ClusterAwsResponse,
    ClusterAwsUpdate,
    ClusterAzureRequest,
    ClusterAzureResponse,
    ClusterAzureUpdate,
    ClusterFeature,
    ClusterLock,
    ClusterLockRead,
)
from api.shared.models.features import Feature, FeatureBaseEnable
from api.shared.models.nodes import AdditionalNodePool
from api.shared.models.storage_classes import StorageClass, StorageClassBase
from api.shared.models.teams_webhooks import TeamsWebhook, TeamsWebhookRequest
from api.shared.models.user_features import UserFeature, UserFeatureBase
from api.shared.repository.feature_repository import FeatureRepository
from api.shared.repository.release_repository import ReleaseRepository


class ClusterRepository:
    session: Session
    feature_repository: FeatureRepository
    release_repository: ReleaseRepository

    def __init__(
        self,
        session: Session = Depends(get_db),
        feature_repository: FeatureRepository = Depends(FeatureRepository),
        release_repository: ReleaseRepository = Depends(ReleaseRepository),
    ):
        self.session = session
        self.feature_repository = feature_repository
        self.release_repository = release_repository

    def add_cluster(
        self, cluster_request: Union[ClusterAwsRequest, ClusterAzureRequest]
    ) -> Union[ClusterAwsResponse, ClusterAzureResponse]:
        """
        Adds cluster

        Args:
            cluster_request (Union[ClusterAwsRequest, ClusterAzureRequest]): Cluster request

        Returns:
            Union[ClusterAwsResponse, ClusterAzureResponse]: The created cluster response based on provider
        """
        cluster = Cluster.model_validate(
            self._normalize_nullable_cluster_fields(cluster_request.model_dump()),
            update={
                "features": [],
                "client_namespaces": [],
                "additional_node_pools": [],
                "teams_webhooks": [],
                "client_otlp_endpoints": [],
                "storage_classes": [],
                "user_features": [],
            },
        )

        db_features = self.feature_repository.get_features()

        for cluster_feature in cluster_request.features:
            feature = next(
                (
                    db_feature
                    for db_feature in db_features
                    if db_feature.name == cluster_feature.name
                    and db_feature.type == cluster_feature.type
                    and db_feature.namespaced == cluster_feature.namespaced
                    and db_feature.constraints == cluster_feature.constraints
                ),
                Feature.model_validate(cluster_feature),
            )

            cluster.features.append(
                ClusterFeature(
                    feature=feature,
                    cluster=cluster,
                    enabled=cluster_feature.enabled,
                )
            )

        if cluster_request.client_namespaces:
            for namespace in cluster_request.client_namespaces:
                cluster.client_namespaces.append(ClientNamespace.model_validate(namespace))

        if cluster_request.additional_node_pools:
            for additional_node_pool in cluster_request.additional_node_pools:
                cluster.additional_node_pools.append(AdditionalNodePool.model_validate(additional_node_pool))

        if cluster_request.teams_webhooks:
            webhooks = cluster_request.teams_webhooks.convert_webhooks(cluster.name)
            for webhook in webhooks:
                cluster.teams_webhooks.append(TeamsWebhook.model_validate(webhook))

        if cluster_request.client_otlp_endpoints:
            for otlp_endpoint in cluster_request.client_otlp_endpoints:
                cluster.client_otlp_endpoints.append(ClientOTLPEndpoint.model_validate(otlp_endpoint))

        if cluster_request.provider == Provider.AZURE and cluster_request.storage_classes:
            for storage_class in cluster_request.storage_classes.to_list():
                cluster.storage_classes.append(StorageClass.model_validate(storage_class))

        db_cluster = self.save_cluster(cluster)

        return db_cluster.build_response()

    @staticmethod
    def _normalize_nullable_cluster_fields(data: dict[str, Any]) -> dict[str, Any]:
        nullable_string_fields = {
            "account_name",
            "vpc_endpoint_service_name",
            "vpc_endpoint_service_ingress_name",
            "cluster_oidc_issuer_url",
            "azure_subnet_name",
            "azure_vnet_name",
            "azure_vnet_resource_group",
            "dns_service_ip",
            "mi_agentpool_object_id",
            "mi_cluster_object_id",
        }
        deprecated_fields = {
            "kubedownscaler_downscale_period",
            "kubedownscaler_upscale_period",
        }

        return {
            key: None if key in nullable_string_fields and value == "" else value
            for key, value in data.items()
            if key not in deprecated_fields
        }

    def get_cluster(self, id: int) -> Cluster:
        """
        Gets cluster

        Args:
            id (int): ID

        Returns:
            Cluster: Cluster object
        """
        return self.session.get(Cluster, id)

    def save_cluster(self, cluster: Cluster) -> Cluster:
        """
        Saves cluster

        Args:
            cluster (Cluster): DB Cluster object

        Returns:
            Cluster: Cluster object
        """
        self.session.add(cluster)
        self.session.commit()
        self.session.refresh(cluster)
        return cluster

    def update_cluster(
        self, cluster: Cluster, update_data: Union[ClusterAwsUpdate, ClusterAzureUpdate]
    ) -> Union[ClusterAwsResponse, ClusterAzureResponse]:
        """
        Update cluster

        Args:
            cluster (Cluster): DB Cluster object
            update_data (Union[ClusterAwsUpdate, ClusterAzureUpdate]): Data to update the cluster with

        Raises:
            ReleaseNotFoundException: Release not found

        Returns:
            Union[ClusterAwsResponse, ClusterAzureResponse]: The updated cluster response based on provider
        """
        if update_data.features is not None:  # if is an empty list it should update
            try:
                release_name = update_data.release if update_data.release else cluster.release
                self._update_cluster_features(
                    cluster,
                    release_name,
                    update_data.features,
                )
            except ReleaseNotFoundException:
                raise

        if update_data.user_features is not None:  # if is an empty list it should update
            self._update_user_features(cluster, update_data.user_features)

        if update_data.client_namespaces is not None:
            self._update_client_namespaces(cluster, update_data.client_namespaces)

        if update_data.additional_node_pools is not None:
            self._update_additional_node_pools(cluster, update_data.additional_node_pools)

        if update_data.teams_webhooks is not None:
            self._update_teams_webhooks(cluster, update_data.teams_webhooks)

        if update_data.client_otlp_endpoints is not None:
            self._update_client_otlp_endpoints(cluster, update_data.client_otlp_endpoints)

        if cluster.provider == Provider.AZURE and update_data.storage_classes is not None:
            self._update_storage_classes(cluster, update_data.storage_classes.to_list())

        # Remove fields that are being updated directly on their own methods above
        update_data = self._normalize_nullable_cluster_fields(
            update_data.model_dump(
                exclude={
                    "features",
                    "client_namespaces",
                    "additional_node_pools",
                    "user_features",
                    "teams_webhooks",
                    "client_otlp_endpoints",
                    "storage_classes",
                },
                exclude_unset=True,
            )
        )

        for key, value in update_data.items():
            setattr(cluster, key, value)

        return self.save_cluster(cluster).build_response()

    def _update_additional_node_pools(self, cluster: Cluster, additional_node_pools: List[AdditionalNodePool]) -> None:
        """
        Updates additional node pools

        Args:
            cluster (Cluster): Cluster object
            additional_node_pools (List[AdditionalNodePool]): Node pools to update the cluster with
        """
        updated_additional_np = []

        for requested_additional_np in additional_node_pools:
            db_additional_np = next(
                (
                    db_additional_np
                    for db_additional_np in cluster.additional_node_pools
                    if db_additional_np.name == requested_additional_np.name
                ),
                None,
            )

            if db_additional_np:  # Update
                additional_np = AdditionalNodePool.model_validate(
                    db_additional_np.model_dump(), update=requested_additional_np.model_dump()
                )
                # model_validate creates a new detached instance with an existing PK.
                # merge() reattaches it to the session's identity map so changes are persisted.
                additional_np = self.session.merge(additional_np)
            else:  # create
                additional_np = AdditionalNodePool.model_validate(requested_additional_np)

            updated_additional_np.append(additional_np)

        cluster.additional_node_pools = updated_additional_np
        self.save_cluster(cluster)

    def _update_client_namespaces(self, cluster: Cluster, client_namespaces: List[ClientNamespace]) -> None:
        """
        Updates client namespaces

        Args:
            cluster (Cluster): Cluster object
            client_namespaces (List[ClientNamespace]): Client namespaces to update the cluster with
        """
        updated_client_ns = []

        for requested_client_ns in client_namespaces:
            db_client_ns = next(
                (
                    db_client_ns
                    for db_client_ns in cluster.client_namespaces
                    if db_client_ns.name == requested_client_ns.name
                ),
                None,
            )

            if db_client_ns:  # Update
                client_ns = ClientNamespace.model_validate(
                    db_client_ns.model_dump(), update=requested_client_ns.model_dump()
                )
                client_ns = self.session.merge(client_ns)
            else:  # create
                client_ns = ClientNamespace.model_validate(requested_client_ns)

            updated_client_ns.append(client_ns)

        cluster.client_namespaces = updated_client_ns
        self.save_cluster(cluster)

    def _update_user_features(self, cluster: Cluster, user_features: List[UserFeatureBase]) -> None:
        """
        Updates user features

        Args:
            cluster (Cluster): Cluster object
            user_features (List[UserFeatureBase]): User features to update the cluster with
        """
        # Create a new list of cluster features
        updated_user_features = []

        for requested_user_feature in user_features:
            db_user_feature = next(
                (
                    db_user_feature
                    for db_user_feature in cluster.user_features
                    if db_user_feature.name == requested_user_feature.name
                ),
                None,
            )

            if db_user_feature:  # Update
                user_feature = UserFeature.model_validate(
                    db_user_feature.model_dump(), update=requested_user_feature.model_dump()
                )
                user_feature = self.session.merge(user_feature)
            else:  # create
                data = {**requested_user_feature.model_dump(), "cluster_id": cluster.id}
                user_feature = UserFeature.model_validate(data)

            updated_user_features.append(user_feature)

        cluster.user_features = updated_user_features
        self.save_cluster(cluster)

    def _update_cluster_features(
        self,
        cluster: Cluster,
        release_name: str,
        data_features: List[FeatureBaseEnable],
    ) -> None:
        """
        Updates cluster features

        Args:
            cluster (Cluster): Cluster object
            release_name (str): Release name
            data_features (List[FeatureBaseEnable]): Data to update the cluster with

        Raises:
            ReleaseNotFoundException: ReleaseNotFoundException
        """

        if data_features:
            # Create a new list of cluster features
            updated_cluster_features = []

            enabled_optional_features = {
                data_feature.name: data_feature for data_feature in data_features if data_feature.enabled
            }

            try:
                release = self.release_repository.get_releases(name=release_name.lower(), provider=cluster.provider)[0]
            except IndexError as err:
                raise ReleaseNotFoundException(f"Release {release_name} not found") from err

            for release_feature in release.features:
                feature = release_feature.feature

                # Return the existing cluster-features if it exists
                # else, create a new one
                cluster_feature = next(
                    (cluster_feature for cluster_feature in cluster.features if feature == cluster_feature.feature),
                    ClusterFeature(
                        cluster_id=cluster.id,
                        feature_id=feature.id,
                    ),
                )

                # Enable/Disable the feature
                if feature.name in enabled_optional_features:
                    cluster_feature.enabled = enabled_optional_features[feature.name].enabled
                    cluster_feature.config = enabled_optional_features[feature.name].config
                else:
                    cluster_feature.enabled = False
                    cluster_feature.config = None

                # Append to cluster features
                updated_cluster_features.append(cluster_feature)

            # Replace features with new list
            cluster.features = updated_cluster_features

            # Save cluster
            self.save_cluster(cluster)

    def _update_teams_webhooks(self, cluster: Cluster, teams_webhooks_request: TeamsWebhookRequest) -> None:
        """
        Updates teams webhooks for a cluster.
        - Webhooks in the request but not in DB will be created
        - Webhooks in DB but not in request will be deleted
        - Webhooks in both will be kept unchanged

        Args:
            cluster (Cluster): The cluster to update
            teams_webhooks_request (TeamsWebhookRequest): The webhooks list to sync with
        """
        requested_webhooks = teams_webhooks_request.convert_webhooks(cluster.name)

        existing_webhook_ids = {w.webhook_id for w in cluster.teams_webhooks}
        requested_webhook_ids = {w.webhook_id for w in requested_webhooks}

        # Webhooks to delete (in DB but not in request)
        to_delete_ids = existing_webhook_ids - requested_webhook_ids
        # Webhooks to add (in request but not in DB)
        to_add_ids = requested_webhook_ids - existing_webhook_ids

        # Keep existing webhooks
        final_webhooks = [w for w in cluster.teams_webhooks if w.webhook_id not in to_delete_ids]

        # Add new webhooks
        for webhook in requested_webhooks:
            if webhook.webhook_id in to_add_ids:
                final_webhooks.append(TeamsWebhook.model_validate(webhook))

        # Save cluster
        cluster.teams_webhooks = final_webhooks
        self.save_cluster(cluster)

    def _update_client_otlp_endpoints(self, cluster, client_otlp_endpoints: List[ClientOTLPEndpointBase]) -> None:
        """
        Updates client otlp endopints

        Args:
            cluster (Cluster): Cluster object
            client_otlp_endpoints (List[ClientOTLPEndpointBase]): Client otlp endopints to update the cluster with
        """
        updated_client_otlp_endpoints = []

        for requested_client_otlp_endpoint in client_otlp_endpoints:
            db_client_otlp_endpoint = next(
                (
                    db_client_otlp_endpoint
                    for db_client_otlp_endpoint in cluster.client_otlp_endpoints
                    if db_client_otlp_endpoint.name == requested_client_otlp_endpoint.name
                ),
                None,
            )

            if db_client_otlp_endpoint:  # Update
                client_otlp = ClientOTLPEndpoint.model_validate(
                    db_client_otlp_endpoint.model_dump(), update=requested_client_otlp_endpoint.model_dump()
                )
                client_otlp = self.session.merge(client_otlp)
            else:  # create
                client_otlp = ClientOTLPEndpoint.model_validate(requested_client_otlp_endpoint)

            updated_client_otlp_endpoints.append(client_otlp)

        cluster.client_otlp_endpoints = updated_client_otlp_endpoints
        self.save_cluster(cluster)

    def _update_storage_classes(self, cluster: Cluster, storage_classes: List[StorageClassBase]) -> None:
        """
        Updates storage classes

        Args:
            cluster (Cluster): Cluster object
            storage_classes (List[StorageClassBase]): Storage classes to update the cluster with
        """
        updated_storage_classes = []

        for requested_storage_class in storage_classes:
            db_storage_class = next(
                (
                    db_storage_class
                    for db_storage_class in cluster.storage_classes
                    if db_storage_class.name == requested_storage_class.name
                ),
                None,
            )

            if db_storage_class:  # Update
                storage_class = StorageClass.model_validate(
                    db_storage_class.model_dump(), update=requested_storage_class.model_dump()
                )
                storage_class = self.session.merge(storage_class)
            else:  # create
                storage_class = StorageClass.model_validate(requested_storage_class)

            updated_storage_classes.append(storage_class)

        cluster.storage_classes = updated_storage_classes
        self.save_cluster(cluster)

    def update_cluster_status(
        self, cluster: Cluster, new_status: ClusterStatus
    ) -> Union[ClusterAwsResponse, ClusterAzureResponse]:
        """
        Update cluster status

        Args:
            cluster (Cluster): DB Cluster object
            new_status (ClusterStatus): New status to update the cluster with

        Returns:
            Union[ClusterAwsResponse, ClusterAzureResponse]: The updated cluster response based on provider
        """
        cluster.status = new_status

        return self.save_cluster(cluster).build_response()

    def delete_cluster(self, cluster: Cluster) -> dict:
        """
        Deletes cluster

        Args:
            cluster (Cluster): Cluster object

        Returns:
            dict: Cluster deletion information
        """
        self.session.delete(cluster)
        self.session.commit()
        return {"msg": f"Cluster {cluster.name} deleted successfully"}

    def get_cluster_var_by_env(self, var_to_query: str, **filters: Any) -> list[Cluster]:
        """
        Gets cluster variables by environment

        Args:
            var_to_query (str): Variables to query the DB

        Returns:
            list[Cluster]: List of variables
        """
        query = (
            self.session.query(
                Cluster.environment,
                sqlalchemy.func.array_agg(distinct(var_to_query), type_=ARRAY(Integer)).label(var_to_query.key),
            )
            .filter_by(**filters)
            .group_by(Cluster.environment)
        )

        return query.all()

    def get_clusters_with_adgr_groups(self, adgr_groups: List[str]):
        """
        Gets clusters with ADGR groups

        Args:
            adgr_groups (List[str]): List of ADGR groups

        Returns:
            List[Union[ClusterAwsResponse, ClusterAzureResponse]]: List of parsed clusters
        """
        statement = (
            select(Cluster)
            .join(ClientNamespace, Cluster.id == ClientNamespace.cluster_id)
            .where(
                or_(
                    ARRAY.Comparator.overlap(ClientNamespace.admin, adgr_groups),
                    ARRAY.Comparator.overlap(ClientNamespace.editor, adgr_groups),
                    ARRAY.Comparator.overlap(ClientNamespace.viewer, adgr_groups),
                )
            )
            .order_by(asc(ClientNamespace.id))
        )
        result = self.session.execute(statement).unique()
        clusters: List[Cluster] = result.scalars().all()
        return [cluster.build_response() for cluster in clusters]

    def get_clusters_v2(
        self,
        condition_filters: list,
        locked: bool = None,
        order_by: str = "id",
    ) -> list[Cluster]:
        """
        Gets clusters information

        Args:
            condition_filters (list): Condition filters
            locked (bool, optional): Cluster lock. Defaults to None.
            order_by (str, optional): Order by. Defaults to "id".

        Returns:
            list[Cluster]: List of clusters information.
        """
        now = datetime.now(tz=timezone.utc).replace(tzinfo=None)  # Create timestamp in UTC

        query = (
            select(Cluster)
            .filter(*condition_filters)
            .join(ClusterLock, Cluster.id == ClusterLock.cluster_id, isouter=not locked)  # Left outer join
            .order_by(asc(getattr(Cluster, order_by)))
        )

        if locked:
            query = query.where(
                and_(
                    ClusterLock.locked == locked,  # Return when Locked is True
                    ClusterLock.timeout_at > now,
                )
            )  # if hasn't timed out
        elif locked is False:
            query = query.where(
                or_(
                    ClusterLock.locked.isnot(True),  # To return clusters where Locked is null or False
                    ClusterLock.timeout_at < now,
                )  # To return clusters where Locked is True but timed out
            )
        result = self.session.execute(query).unique()
        return result.scalars().all()

    # To be deprecated after owner_group is updated in the database to lowercase
    def get_clusters_v1(
        self,
        filters: dict,
        locked: bool = None,
        order_by: str = "id",
    ) -> list[Cluster]:
        """
        Gets clusters information

        Args:
            filters (dict): Filters
            locked (bool, optional): Cluster lock. Defaults to None.
            order_by (str, optional): Order by. Defaults to "id".

        Returns:
            list[Cluster]: List of clusters information.
        """
        now = datetime.now(tz=timezone.utc).replace(tzinfo=None)  # Create timestamp in UTC

        owner_group = filters.pop("owner_group", None)

        query = (
            select(Cluster)
            .filter_by(**filters)
            .join(ClusterLock, Cluster.id == ClusterLock.cluster_id, isouter=not locked)  # Left outer join
            .order_by(asc(getattr(Cluster, order_by)))
        )

        if owner_group:
            query = query.filter(Cluster.owner_group.ilike(owner_group))

        if locked:
            query = query.where(
                and_(
                    ClusterLock.locked == locked,  # Return when Locked is True
                    ClusterLock.timeout_at > now,
                )
            )  # if hasn't timed out
        elif locked is False:
            query = query.where(
                or_(
                    ClusterLock.locked.isnot(True),  # To return clusters where Locked is null or False
                    ClusterLock.timeout_at < now,
                )  # To return clusters where Locked is True but timed out
            )

        result = self.session.execute(query).unique()
        return result.scalars().all()

    def get_cluster_locks(self, **filters: Any) -> List[ClusterLockRead]:
        """
        Gets clusters locks

        Returns:
            List[ClusterLockRead]: List of clusters locks
        """
        cluster_name = filters.pop("cluster_name", None)

        query = select(ClusterLock, Cluster.name).join(Cluster, Cluster.id == ClusterLock.cluster_id)

        for key, value in filters.items():
            query = query.where(getattr(ClusterLock, key) == value)
        if cluster_name is not None:
            query = query.where(Cluster.name == cluster_name)

        rows = self.session.execute(query).all()
        return [
            ClusterLockRead(
                cluster_name=name,
                locked=lock.locked,
                owner=lock.owner,
                token=lock.token,
                timeout_at=lock.timeout_at,
                created_at=lock.created_at,
                updated_at=lock.updated_at,
            )
            for lock, name in rows
        ]

    def lock_cluster(self, cluster: Cluster, owner: str, timeout: int) -> str:
        """
        Locks clusters

        Args:
            cluster (Cluster): Cluster to lock
            owner (str): Lock owner
            timeout (int): Timeout

        Raises:
            LockException: LockException

        Returns:
            str: Lock token
        """
        lock: Optional[ClusterLock] = self.session.get(
            ClusterLock,
            cluster.id,
            with_for_update={"nowait": True},
        )

        now = datetime.now(tz=timezone.utc).replace(tzinfo=None)  # Create timestamp in UTC
        timeout_dt = now + timedelta(minutes=timeout)  # Calculate timeout
        token = str(uuid4())

        if not lock:  # Lock does not exist
            lock = ClusterLock(
                cluster_id=cluster.id,
                created_at=now,
                updated_at=now,
                owner=owner,
                locked=True,
                token=token,
                timeout_at=timeout_dt,
            )
            logger.info(f"Lock for cluster {cluster.name} will be created")
        else:  # Lock exists
            if lock.locked:  # Check if lock timed out
                if now < lock.timeout_at:
                    # Lock exists and is not timed out
                    raise LockException(f"Cluster {cluster.name} is already locked by another operation")

                logger.warning(f"Cluster lock for {cluster.name} will be overwritten because it has timed out")

            lock.owner = owner
            lock.token = token
            lock.updated_at = now
            lock.locked = True
            lock.timeout_at = timeout_dt

        self.session.add(lock)
        self.session.commit()
        self.session.refresh(lock)

        logger.info(f"Cluster {cluster.name} was locked")
        return token

    def unlock_cluster(self, cluster: Cluster, token: str) -> bool:
        """
        Unlocks clusters

        Args:
            cluster (Cluster): Cluster to unlock
            token (str): Token

        Raises:
            LockException: Cluster does not have a lock
            LockException: Cluster is not locked
            LockException: Lock token did not match

        Returns:
            bool: True
        """
        lock: Optional[ClusterLock] = self.session.get(
            ClusterLock,
            cluster.id,
            with_for_update={"nowait": True},
        )

        if not lock:
            raise ClusterLockNotFoundException(f"The cluster {cluster.name} does not have a lock")
        elif not lock.locked:
            raise ClusterNotLockedException(f"The cluster {cluster.name} is not locked")
        elif lock.token != token:
            raise LockTokenMismatchException(f"The cluster {cluster.name} lock token did not match")

        lock.owner = None
        lock.token = None
        lock.updated_at = datetime.today()
        lock.locked = False

        self.session.add(lock)
        self.session.commit()
        self.session.refresh(lock)
        logger.info(f"Cluster {cluster.name} was unlocked")
        return True
