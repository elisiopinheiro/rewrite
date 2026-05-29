"""Shared enums for the API contract."""

from enum import StrEnum


class Provider(StrEnum):
    AWS = "aws"
    AZURE = "azure"


class Environment(StrEnum):
    TEST = "test"
    DEV = "development"
    INT = "integration"
    PRE_PROD = "pre-production"
    PROD = "production"


class ClusterStatus(StrEnum):
    RUNNING = "running"
    FREEZE = "freeze"


class AzureSkuTier(StrEnum):
    FREE = "Free"
    STANDARD = "Standard"


class ClusterOrderBy(StrEnum):
    ID = "id"
    NAME = "name"
    CMDB_APP_ID = "cmdb_app_id"


class ReleaseOrderBy(StrEnum):
    ID = "id"
    NAME = "name"
