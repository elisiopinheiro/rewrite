"""ORM table definitions for Alembic discovery."""

from app.models.base import Base
from app.models.cluster import Cluster, ClusterFeature
from app.models.feature import Feature
from app.models.lock import ClusterLock
from app.models.namespace import ClientNamespace
from app.models.node_pool import AdditionalNodePool
from app.models.operation import Operation
from app.models.otlp_endpoint import ClientOTLPEndpoint
from app.models.release import Release, ReleaseFeature
from app.models.storage_class import StorageClass
from app.models.user_feature import UserFeature
from app.models.webhook import TeamsWebhook

__all__ = [
    "AdditionalNodePool",
    "Base",
    "ClientNamespace",
    "ClientOTLPEndpoint",
    "Cluster",
    "ClusterFeature",
    "ClusterLock",
    "Feature",
    "Operation",
    "Release",
    "ReleaseFeature",
    "StorageClass",
    "TeamsWebhook",
    "UserFeature",
]
